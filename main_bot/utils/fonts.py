def fancy_title(text: str) -> str:
    """
    Convert A–Z to a boxed fancy style used for titles.
    Example: FILE → 🅵🅸🅻🅴
    """
    mapping = str.maketrans({
        "A": "🅰", "B": "🅱", "C": "🅲", "D": "🅳",
        "E": "🅴", "F": "🅵", "G": "🅶", "H": "🅷",
        "I": "🅸", "J": "🅹", "K": "🅺", "L": "🅻",
        "M": "🅼", "N": "🅽", "O": "🅾", "P": "🅿",
        "Q": "🆀", "R": "🆁", "S": "🆂", "T": "🆃",
        "U": "🆄", "V": "🆅", "W": "🆆", "X": "🆇",
        "Y": "🆈", "Z": "🆉",
    })
    return text.upper().translate(mapping)


def italic(text: str) -> str:
    """
    Convert normal letters to italic Unicode.
    Used for 'please wait…' and soft text.
    """
    base = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    italic_chars = (
        "𝘈𝘉𝘊𝘋𝘌𝘍𝘎𝘏𝘐𝘑𝘒𝘓𝘔𝘕𝘖𝘗𝘘𝘙𝘚𝘛𝘜𝘝𝘞𝘟𝘠𝘡"
        "𝘢𝘣𝘤𝘥𝘦𝘧𝘨𝘩𝘪𝘫𝘬𝘭𝘮𝘯𝘰𝘱𝘲𝘳𝘴𝘵𝘶𝘷𝘸𝘹𝘺𝘻"
    )
    table = str.maketrans({base[i]: italic_chars[i] for i in range(len(base))})
    return text.translate(table)


def superscript(text: str) -> str:
    """
    Convert digits and some letters to superscript.
    Used in soft descriptions like 'ᵀʸᵖᵉ ˢᵒᵐᵉᵗʰⁱⁿᵍ'.
    """
    mapping = {
        "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
        "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹",

        "a": "ᵃ", "b": "ᵇ", "c": "ᶜ", "d": "ᵈ", "e": "ᵉ",
        "f": "ᶠ", "g": "ᵍ", "h": "ʰ", "i": "ⁱ", "j": "ʲ",
        "k": "ᵏ", "l": "ˡ", "m": "ᵐ", "n": "ⁿ", "o": "ᵒ",
        "p": "ᵖ", "r": "ʳ", "s": "ˢ", "t": "ᵗ", "u": "ᵘ",
        "v": "ᵛ", "w": "ʷ", "x": "ˣ", "y": "ʸ", "z": "ᶻ",

        " ": " ",
    }

    return "".join(mapping.get(ch.lower(), ch) for ch in text)
