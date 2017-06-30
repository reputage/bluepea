#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
BluePea server daemon CLI

Runs ioflo plan from command line shell

example production:

bluepead -v concise -r -p 0.0625 -n bluepea -f flo/main.flo -b bluepea.core

bluepead -v concise -r -p 0.0625 -n bluepea -f /Data/Code/private/indigo/bluepea/src/bluepea/flo/main.flo -b bluepea.core

example testing:

bluepead -v concise -r -p 0.0625 -n bluepea -f flo/test.flo -b bluepea.core

"""
import sys
import ioflo.app.run

def main():
    """ Main entry point for ioserve CLI"""
    from bluepea import __version__
    args = ioflo.app.run.parseArgs(version=__version__)  # inject  version here

    ioflo.app.run.run(  name=args.name,
                        period=float(args.period),
                        real=args.realtime,
                        retro=args.retrograde,
                        filepath=args.filename,
                        behaviors=args.behaviors,
                        mode=args.parsemode,
                        username=args.username,
                        password=args.password,
                        verbose=args.verbose,
                        consolepath=args.console,
                        statistics=args.statistics)

if __name__ == '__main__':
    main()
