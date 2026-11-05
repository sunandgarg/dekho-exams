import argparse

def positive_integer(text):
    value = int(text)
    if value <= 0:
        raise argparse.ArgumentTypeError("positive integer required")
    return value

def parser():
    options = argparse.ArgumentParser(exit_on_error=False)
    options.add_argument("--quantity", type=positive_integer, required=True)
    options.add_argument("--unit-minor", type=positive_integer, required=True)
    return options

if __name__ == "__main__":
    options = parser().parse_args(["--quantity", "3", "--unit-minor", "125"])
    print(options.quantity * options.unit_minor)
    try:
        parser().parse_args(["--quantity", "-1", "--unit-minor", "125"])
    except argparse.ArgumentError:
        print("option rejected")
