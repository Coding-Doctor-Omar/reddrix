from camoufox.pkgman import CamoufoxFetcher
import argparse


def install_binary():
    CamoufoxFetcher().install(replace=True)

def main():
    parser = argparse.ArgumentParser(prog="reddrix", description="Reddrix --- all-in-one Reddit scraper")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser(
        name="install",
        help="Installs the Camoufox binary dependency."
    )
    
    args = parser.parse_args()
    
    if args.command == "install":
        install_binary()
    else:
        print(f"[reddrix] `{args.command}` is not a valid command.", flush=True)
        parser.print_help()

if __name__ == "__main__":
    main()
