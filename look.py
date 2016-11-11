#!/usr/bin/env python

import os
import sys
import utils
import oneRun
import printer
from options import opts
from configuration.sw import eosprefix


def eos():
    #################################
    # NOTES from local installation #
    #################################
    # rsync -av lxplus.cern.ch:/afs/cern.ch/project/eos/installation/0.3.84-aquamarine .
    # emerge -av readline:5
    # /usr/lib # ln -s libcrypto.so libcrypto.so.6
    # edit 0.3.84-aquamarine/bin/eos.select :
    # export EOSSYS=${HOME}/0.3.84-aquamarine
    # export EOS_MGM_URL=root://eoscms.cern.ch
    ################################################

    for d in ["/afs/cern.ch/project/eos/installation", os.environ["HOME"]]:
        f = "%s/0.3.84-aquamarine/bin/eos.select" % d
        if os.path.exists(f):
            return f

    sys.exit("ERROR: could not find eos.")


def find1(run):
    for local in ["/tmp/USC_%d.root" % run, "data/USC_%d.root" % run, "data/run%d.root" % run, "/uscms/home/jhakala/nobackup/FNAL_%06d.root" % run]:
        if os.path.exists(local):
            return local


def find2(run):
    USC = "/store/group/dpg_hcal/comm_hcal/USC/USC_%d.root" % run
    stat = "%s stat %s" % (eos(), USC)
    if not utils.commandOutputFull(stat)["returncode"]:
        return "%s/%s" % (eosprefix, USC)


def find_gr(run, grdir, hhmmMin=None, quiet=False):
    d = "%s/000/%03d/%03d/00000/" % (grdir, run/1000, run % 1000)
    stat = "%s stat %s" % (eos(), d)
    ls = stat.replace(" stat ", " ls -l ")

    if utils.commandOutputFull(stat)["returncode"]:
        return

    listings = filter(lambda x: x, utils.commandOutputFull(ls)["stdout"].split("\n"))

    month_num = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr":  4, "May":  5, "Jun":  6,
                 "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}

    coords = []
    for listing in listings:
        fields = listing.split()
        month, day, hhmm, fileName = fields[-4:]
        hh, mm = hhmm.split(":")
        coords.append((month_num[month], int(day), int(hh), int(mm), fileName))

    coords.sort()
    if hhmmMin:
        mmMin = hhmmMin % 100
        hhMin = hhmmMin / 100
        coords = filter(lambda x: hhMin < x[2] or (hhMin == x[2] and mmMin <= x[3]), coords)
        if not quiet:
            for c in coords:
                print c

    files = [c[-1] for c in coords]
    if files:
        l = ",".join(["%s/%s%s" % (eosprefix, d, f) for f in files])
        return l


def report(fileNames, iFind):
    pieces = [f.split("/") for f in fileNames]
    bases = set(["/".join(piece[:-1]) for piece in pieces])
    assert len(bases) == 1, bases
    if len(fileNames) == 1 and iFind <= 2:
        print "Found matching file: %s" % fileNames[0]
    else:
        print "Found %4d file(s) in %s/" % (len(fileNames), "/".join(bases))


def override(options, quiet, run):
    if not options.nEvents:
        options.nEvents = 10

    options.progress = not quiet
    if options.dump == -1 and not quiet:
        options.dump = 0

    # handle old BcN (http://cmsonline.cern.ch/cms-elog/849949)
    if run <= 240698:
        options.utcaBcnDelta = -131
    else:
        options.utcaBcnDelta = 0


def main(options, args, quiet=False):
    if len(args) != 1:
        sys.exit("Please provide a run number as the argument.")
    try:
        run = int(args[0])
    except ValueError:
        sys.exit("Could not convert %s to int." % args[0])

    #subdet = "HBHE" if not options.hf else "HF"
    subdet = "FNAL"
    options.feds1 = subdet
    # options.feds2 = "v%s" % subdet
    options.outputFile = "output/%d_%s.root" % (run, subdet)

    override(options, quiet, run)

    if options.noLoop:  # skip file finding
        options.file1 = "dummy"
        oneRun.main(options)
        return

    paths = {1: None, 2: None}
    if run < 246908:  # 2015-06-03  first 13 TeV stable beams
        paths.update({3: "/store/data/Commissioning2015/HcalNZS/RAW/v1",
                      4: "/store/express/Commissioning2015/ExpressPhysics/FEVT/Express-v1",
                      5: "/store/express/Commissioning2015/ExpressCosmics/FEVT/Express-v1",
                      6: "/store/data/Commissioning2015/Cosmics/RAW/v1",
                      7: "/store/data/Commissioning2015/MinimumBias/RAW/v1",
                      })
    elif run < 250985:
        paths.update({# 3: "/store/data/Run2015A/HcalNZS/RAW/v1",
                      4: "/store/express/Run2015A/ExpressPhysics/FEVT/Express-v1/",
                      })

    else:
        paths.update({3: "/store/data/Run2016A/HcalNZS/RAW/v1",
                      4: "/store/data/Run2016A/ZeroBias1/RAW/v1",
                      })

    for iFind, grDir in sorted(paths.iteritems()):
        if grDir is None:
            options.file1 = eval("find%d" % iFind)(run)
        else:
            options.file1 = find_gr(run, grDir, options.hhmm, quiet)

        if not options.file1:
            continue

        fileNames = options.file1.split(",")
        report(fileNames, iFind)

        n = len(fileNames)
        if 2 <= n and options.hhmm is None:
            options.sparseLoop = max(1, options.nEvents / n)
        else:
            options.sparseLoop = -1

        options.file2 = ""  # clear from previous iterations
        if oneRun.main(options):
            continue
        else:
            return

    printer.warning("Did not find a matching file for run %d.  Perhaps try 'source env/lxplus6.sh'" % run)
    return 1


if __name__ == "__main__":
    main(*opts(alsoArgs=True))
