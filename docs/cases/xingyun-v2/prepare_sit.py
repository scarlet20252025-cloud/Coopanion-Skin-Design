"""Register the approved seated painting against Xingyun's neck and shoulders."""
from assemble import OUT, WORK, clean, read, warp, write


def main():
    body = clean(read(WORK / "sit-body-approved.png"))
    # Match torso width at the shoulder buckles, then align the neck opening.
    scale = .57
    matrix = ((scale, 0, 658 - 650 * scale), (0, scale, 645 - 224 * scale))
    write(OUT / "sitBody.png", clean(warp(body, matrix)))


if __name__ == "__main__":
    main()
