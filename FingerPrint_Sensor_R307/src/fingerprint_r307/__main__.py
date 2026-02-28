"""
Main entry point for the fingerprint_r307 package.
Allows running the package as a module: python -m fingerprint_r307
"""
import sys
import argparse


def main():
    """Main entry point for command-line interface."""
    parser = argparse.ArgumentParser(
        description='R307 Fingerprint Sensor Interface',
        epilog='Use subcommands for specific functionality'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Admin subcommand
    subparsers.add_parser('admin', help='Launch admin configuration interface')
    
    # Reader subcommand
    subparsers.add_parser('reader', help='Launch fingerprint reader')
    
    args = parser.parse_args()
    
    if args.command == 'admin':
        from fingerprint_r307.admin.cli import main as admin_main
        admin_main()
    elif args.command == 'reader':
        from fingerprint_r307.reader.verifier import main as reader_main
        reader_main()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
