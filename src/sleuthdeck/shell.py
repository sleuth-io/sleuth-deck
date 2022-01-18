import subprocess


def run(cmd, *args) -> str:
    process = subprocess.run([cmd] + list(args), stdout=subprocess.PIPE, text=True)
    return process.stdout
