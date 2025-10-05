from sys import stdout


def loading_bar(iteration, total, prefix="", suffix="", length=25, fill="█"):
    percent = 100 * (iteration / float(total))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + "-" * (length - filled_length)

    stdout.write(f"\r{prefix} |{bar}| {percent:.1f}% {suffix}")
    stdout.flush()

    # Print newline on complete
    if iteration == total:
        print()
