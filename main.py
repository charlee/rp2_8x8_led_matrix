import time
import rp2
from machine import Pin

@rp2.asm_pio(
    set_init=rp2.PIO.OUT_LOW,
    out_init=rp2.PIO.OUT_LOW,
    sideset_init=rp2.PIO.OUT_LOW,
    autopull=True
)
def led_matrix():
    """
    Send two bytes (16 bits) to the DATA pin,
    one bit per cycle. Then create a pulse on
    the LATCH pin to display the 16 bits.
    """
    set(x, 15)                       # loop counter, loop 16 times
    label('bitloop')
    out(pins, 1)       .side(1)      # {1} mov 1bit to DATA pin
                                     #     and set CLOCK high
    jmp(x_dec, 'delay')              # {2} jump to 'delay'
    set(pins, 1)                     # {3} set LATCH high
    set(x, 15)         .side(0)      # {4} reset counter
    set(pins, 0)                     # {5} set LATCH low
    jmp('bitloop')                   # {6} restart loop
    label('delay')
    nop()                            # {3}
    jmp('bitloop')     .side(0)  [2] # {4-6}

sm = rp2.StateMachine(0, led_matrix, freq=81920,
                      sideset_base=Pin(2),    # CLOCK pin
                      set_base=Pin(4),        # LATCH pin
                      out_base=Pin(3),        # DATA pin
                     )

smily_face = bytes((0x3c, 0x42, 0xa5, 0x81, 0xa5, 0x99, 0x42, 0x3c))
letter_a = bytes((0x18, 0x24, 0x42, 0x42, 0x7e, 0x42, 0x42, 0x42))

def convert_data(data):
    """Convert image data to the format consumable by
    the state machine. sm.put() requires a 32-bit word,
    so the converted image consists of 4 words, in the format of
    <row-selector-1, data-row-1, row-selector-2, data-row-2>

    The 4 words are:
      1: <0xfe, row-1, 0xfd, row-2>
      2: <0xfb, row-3, 0xf7, row-4>
      3: <0xef, row-5, 0xdf, row-6>
      4: <0xbf, row-7, 0x7f, row-8>
      
    """
    converted = []
    for i in range(0, len(smily_face), 2):
        converted.append(
            (~(1 << i) & 0xff) << 24 |
            data[i] << 16 |
            (~(1 << (i+1)) & 0xff) << 8 |
            data[i+1]
        )

    return converted

sm.active(1)

while True:
    for value in convert_data(letter_a):
        sm.put(value)

    #time.sleep_ms(1)

