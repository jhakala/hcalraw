from configuration import hw
import printer


def printraw(raw1={}, raw2={}, **_):
    dump = raw1.get(None, {}).get("dump", -99)
    if 1 <= dump:
        slim1 = (dump in [1, 4]) and (len(raw1) == 2) and (not raw2)
        oneEvent(raw1, slim1=slim1)
        oneEvent(raw2)


def oneEvent(d={}, slim1=False):
    if None not in d:
        return

    aux = d[None]

    if not slim1:
        printer.purple("-" * 86)
        printer.purple("%4s iEntry 0x%08x (%d)" % (aux["label"], aux["iEntry"], aux["iEntry"]))

    printHeaders = not (slim1 and aux["iEntry"])
    for fedId, data in sorted(d.iteritems()):
        if fedId is None:
            continue
        if data["other"]:
            if "magic" in data["other"]:
                oneFedBu(data["other"])
            else:
                oneFedMol(data["other"])

        oneFedHcal(data,
                   dump=aux["dump"],
                   crateslots=aux["crateslots"],
                   nonMatchedQie=aux.get("misMatched", []),
                   nonMatchedTp=aux.get("tMisMatched", []),
                   printHeaders=printHeaders,
                   nTsMax=aux["firstNTs"],
                   )
        printHeaders = True
    if not slim1:
        print


def htrOverview(d={}):
    abbr = "HTR" if "HTR0" in d else "uHTR"
    hyphens = "   "+("-"*(67 if (abbr == "uHTR") else 82))
    printer.cyan(hyphens)

    htr = ["  ", "   %4s" % abbr]
    epcv = ["  ", "   EPCV"]
    lms = ["  ", "    LMS"]
    nWord16 = ["  ", "nWord16"]
    for iHtr in range(15):
        key = "%s%d" % (abbr, iHtr)
        if key not in d:
            continue
        h = d[key]
        htr.append("%4d" % iHtr)
        epcv.append("%d%d%d%d" % (h["E"], h["P"], h["C"], h["V"]))
        if "L" in h:
            lms.append(" %d%d%d" % (h["L"], h["M"], h["S"]))
        nWord16.append("%4d" % (h["nWord16"]))

    lines = [htr] + ([lms] if 3 <= len(lms) else []) + [epcv, nWord16]
    for line in lines:
        printer.cyan(" ".join(line))
    printer.cyan(hyphens)


def oneHtr(iBlock=None, p={}, dump=None, utca=None,
           nonMatchedQie=[], nonMatchedTp=[], nTsMax=None):

    try:
        zs = p.get("ZS")
    except TypeError as e:
        print "iBlock='%s':" % str(iBlock), e
        return

    if "nWord16Qie" in p:
        col = "nWord16Qie"
    elif utca:
        col = "DataLength16"
    elif p.get("IsTTP"):
        col = "          "
    else:
        coords = "crate %2d slot %2d%1s" % (p.get("Crate", -1), p.get("Slot", -1), p.get("Top", "x"))
        printer.warning("unpacking did not succeed enough to print more about %s" % coords)
        return

    columns = ["iWord16",
               "    EvN",
               "  OrN5",
               " BcN",
               "Cr",
               "Sl",
               " Fl",
               "FrmtV",
               "nPre",
               col,
              ]
    if zs:
        columns += [" ", "ZSMask:  Thr1, Thr24, ThrTP"]

    strings = [" %05d" % p["0Word16"],
               " 0x%07x" % p["EvN"],
               "0x%02x" % p["OrN5"],
               "%4d" % p["BcN"],
               "%2d" % p["Crate"],
               "%2d%1s" % (p["Slot"], p["Top"]),
               "%2d" % p.get("FWFlavor", -1),  # absent in uHTR
               " 0x%01x" % p["FormatVer"],
               "  %2d" % p["nPreSamples"],
               ]
    if utca:
        s = "  %4d/%4d" % (p.get(col, -1), p.get(col+"T", -1))
        strings.append(s)
    else:
        strings.append("     %3d " % p.get(col, -1))

    if utca or ("Qie" in col):
        strings.append("      ")
    else:
        strings.append("  TTP ")

    if zs:
        strings += ["",
                    "0x%04x" % zs["Mask"],
                    "  %3d" % zs["Threshold1"],
                    "  %3d" % zs["Threshold24"],
                    "  %3d" % zs["ThresholdTP"],
        ]

    out = []
    if (not iBlock) or 4 <= dump:
        out.append("  ".join(columns))

    if dump != 4 and dump != 10:
        out.append("  ".join(strings))
        printer.green("\n".join(out))

    if dump <= 3:
        return

    kargs = {"skipFibers": [0, 1] + range(3, 14) + range(15, 24) if (dump == 4) else [],
             "skipFibChs": [0, 2, 3, 4, 5, 6, 7] if (4 <= dump <= 7) else [],
             "skipErrF": [],
             "nonMatched": nonMatchedQie,
             "latency": p.get("Latency"),
             "zs": p.get("ZS"),
             "nTsMax": nTsMax,
            }
    if dump in [5, 6, 8]:
        kargs["skipErrF"] = [3]
    if dump == 10:
        kargs["skipErrF"] = [0]

    if p["IsTTP"]:
        cd = ttpData(p["ttpInput"], p["ttpOutput"], p["ttpAlgoDep"])
    else:
        cd = htrChannelData(p["channelData"].values(),
                            crate=p["Crate"],
                            slot=p["Slot"],
                            top=p["Top"],
                            **kargs)

    if len(cd) >= 2:
        printer.yellow(cd[0])
        printer.msg("\n".join(cd[1:]))

    if 6 <= dump:
        kargs = {"crate": p["Crate"],
                 "slot": p["Slot"],
                 "top": p["Top"],
                 "nonMatched": nonMatchedTp,
                 "dump": dump,
                 }
        if utca:
            td = uhtrTriggerData(p["triggerData"], **kargs)
        else:
            td = htrTriggerData(p["triggerData"], zs=zs, **kargs)

        if len(td) >= 2:
            printer.yellow(td[0])
            printer.msg("\n".join(td[1:]))


def qieString(qies=[], sois=[], red=False, nMax=10):
    l = []

    for i in range(nMax):
        if i < len(qies):
            s = "%2x" % qies[i]
            if i < len(sois) and sois[i] and not red:
                s = printer.gray(s, False)
            l.append(s)
        else:
            l.append("  ")

    out = " ".join(l)
    if red:
        out = printer.red(out, False)

    if nMax < len(qies):
        out += printer.red("..", False)
    else:
        out += "  "
    return out


def capIdString(caps, sois, nTsMax):
    l = []

    for i in range(nTsMax):
        if i < len(caps) and i < len(sois):
            value = caps[i]
            s = "%1x" % value
            if sois[i]:
                s = printer.gray(s, False)
            l.append(s)
        else:
            l.append(" ")

    out = "".join(l)

    if nTsMax < len(caps):
        out += printer.red("..", False)
    else:
        out += "  "
    return out


def htrTriggerData(d={}, dump=None, crate=None, slot=None, top="", nonMatched=[], zs={}):
    columns = ["SLB-ch", "Peak", "SofI", "TP(hex)  0   1   2   3"]
    if zs:
        columns.append("  ZS?")
    out = ["  ".join(columns)]
    for key, dct in sorted(d.iteritems()):
        slb, ch = key
        z = ""
        soi = ""
        tp = ""
        if (dump <= 8) and not any([dct["TP"]]):
            continue

        for i in range(len(dct["TP"])):
            z += str(int(dct["Z"][i]))
            soi += str(int(dct["SOI"][i]))
            tp += " %3x" % dct["TP"][i]

        if zs:
            marks = zs["TPMarks"]
            iChannel = 4*(slb - 1) + ch
            if iChannel < len(marks):
                m = "y" if marks[iChannel] else "n"
            else:
                m = " "
            tp += " "*5 + m

        one = "  ".join(["  %1d- %1d" % (slb, ch),
                         "%4s" % z,
                         "%4s" % soi,
                         " "*4,
                         tp])
        if (crate, slot, top, key) in nonMatched:
            one = makeRed(one)
        out.append(one)

    return out


def uhtrTriggerData(d={}, dump=None, crate=None, slot=None, top="", nonMatched=[]):
    out = []
    out.append("  ".join([" TPid",
                          "Fl",
                          "  SofI",
                          "   OK",
                          "  TP(hex)",
                          "    ".join([str(i) for i in range(4)])
                          ])
               )
    for channelId, data in sorted(d.iteritems()):
        if (dump <= 8) and not any(data["TP"]):
            continue
        soi = ""
        ok = ""
        tp = ""
        for j in range(len(data["SOI"])):
            soi += str(data["SOI"][j])
            ok += str(data["OK"][j])
            tp_s = "%5x" % data["TP"][j]
            if data["SOI"][j]:
                tp_s = printer.gray(tp_s, False)
            if not data["OK"][j]:
                tp_s = printer.red(tp_s, False)
            tp += tp_s

        if dump != 10 or not all(data["OK"]):
            out.append("   ".join([" 0x%02x" % channelId,
                                   "%1d" % data["Flavor"],
                                   "%5s" % soi,
                                   "%5s" % ok,
                                   " "*2,
                                   tp]))
    return out


def htrChannelData(lst=[], crate=0, slot=0, top="",
                   skipFibers=[], skipFibChs=[], skipErrF=[],
                   nonMatched=[], latency={}, zs={}, te_tdc=False, nTsMax=None):
    out = []
    columns = ["  Cr",
               "Sl",
               "Fi",
               "Ch",
               "Fl",
               "Er",
               "C0",
               # "C/0" + "".join(["%1x" % i for i in range(1, nTsMax)]),
               # "K/0" + "".join(["%1x" % i for i in range(1, nTsMax)]),
               "0xA0 " + " ".join(["A%1d" % i for i in range(1, nTsMax)]),
               "0xL0 " + " ".join(["L%1d" % i for i in range(1, nTsMax)]),
               ]
    if te_tdc:
        columns += ["0xT0 " + " ".join(["T%1d" % i for i in range(1, nTsMax)])]
    if latency:
        columns += [" EF", "Cnt", "IDLE"]
    if zs:
        columns += [" ", "ZS?"]
    out.append(" ".join(columns))

    for data in sorted(lst, key=lambda x: (x["Fiber"], x["FibCh"])):
        if data["Fiber"] in skipFibers:
            continue
        if data["FibCh"] in skipFibChs:
            continue
        if data["ErrF"] in skipErrF:
            continue
        red = (crate, slot, top, data["Fiber"], data["FibCh"]) in nonMatched

        errf = " %1d" % data["ErrF"]
        if data["ErrF"]:
            errf = printer.red(errf, False)

        fields = ["  %2d" % crate,
                  "%2d%1s%2d" % (slot, top, data["Fiber"]),
                  " %1d" % data["FibCh"],
                  " %1d" % data["Flavor"],
                  errf,
                  " %1d  " % data["CapId"][0],
                  # "  " + capIdString(data["CapId"], data["SOI"], nTsMax),
                  # capIdString(data["OK"], data["SOI"], nTsMax),
                  qieString(data["QIE"], data["SOI"], red=red, nMax=nTsMax),
                  qieString(data.get("TDC", []), data["SOI"], nMax=nTsMax)
                  ]
        if te_tdc:
            fields += [qieString(data.get("TDC_TE", []), data["SOI"], nMax=nTsMax)]
        out.append(" ".join(fields))

        if latency:
            dct = latency.get("Fiber%d" % data["Fiber"])
            if dct and data["FibCh"] == 1:
                lat = ["%s%s" % (dct["Empty"], dct["Full"]),
                       "%2d " % dct["Cnt"],
                       "%4d" % dct["IdleBCN"],
                ]
                out[-1] += " ".join(lat)
        if zs:
            iChannel = 3*(data["Fiber"] - 1) + data["FibCh"]
            marks = zs["DigiMarks"]
            if iChannel < len(marks):
                m = "y" if marks[iChannel] else "n"
            else:
                m = " "
            out[-1] += "%7s" % m

    return out


def ttpData(ttpInput=[], ttpOutput=[], ttpAlgoDep=[]):
    l = []
    columns = ["TS", "0xhgfedcba9876543210", "0x algo", "0xo"]
    l.append("   ".join(columns))

    for i, (inp, out, algo) in enumerate(zip(ttpInput, ttpOutput, ttpAlgoDep)):
        l.append("   ".join(["%2d" % i,
                             "  %018x" % inp,
                             "  %05x" % algo,
                             "  %1x" % out,
                             ])
                 )
    return l


def oneFedHcal(d={}, dump=None, crateslots=[],
               nonMatchedQie=[], nonMatchedTp=[],
               printHeaders=None, nTsMax=None):
    h = d["header"]
    t = d["trailer"]
    if 1 <= dump:
        fields = [" FEDid",
                  "  EvN",
                  "       OrN",
                  "    BcN",
                  "minutes",
                  "TTS",
                  "nBytesHW(   SW)",
                  "type",
                  #"CRC16",
                  "nSkip16",
                  "Blk8",
                  ]

        if printHeaders:
            headers = "  ".join(fields)
            printer.blue("-" * len(headers))
            printer.blue(headers)

        sList = [" %4d" % h["FEDid"],
                 "0x%07x" % h["EvN"],
                 "0x%08x" % h["OrN"],
                 "%4d" % h["BcN"],
                 "%7.3f" % hw.minutes(h["OrN"], h["BcN"]),
                 (" %1x" % t["TTS"]) if "TTS" in t else "  - ",
                 "    %5d(%5d)" % (t["nWord64"]*8 if "nWord64" in t else "  -1", d["nBytesSW"]),
                 "  %1d " % h["Evt_ty"],
                 #(" 0x%04x" % t["CRC16"]) if "CRC16" in t else "   - ",
                 "%7d" % d["nWord16Skipped"],
                 ]
        if h["uFoV"]:
            sList.append("  %2d" % t["Blk_no8"])

        printer.blue("  ".join(sList))
        if 2 <= dump and dump != 4:
            htrOverview(h)

    if dump <= 2:
        return

    for iBlock, block in sorted(d["htrBlocks"].iteritems()):
        if crateslots and (100*block["Crate"] + block["Slot"]) not in crateslots:
            continue
        oneHtr(iBlock=iBlock,
               p=block,
               dump=dump,
               utca=h["utca"],
               nonMatchedQie=nonMatchedQie,
               nonMatchedTp=nonMatchedTp,
               nTsMax=nTsMax,
        )


def oneFedMol(d):
    header = "   ".join([" FEDid  ",
                             "EvN ",
                             "   iBlock",
                             "  nWord64",
                             "magic",
                             ])
    printer.blue("--MOL" + ("-" * len(header)))
    printer.blue(header)

    for iBlock, value in sorted(d.iteritems()):
        printer.blue("   ".join(["  %3d" % value["FEDid"],
                                 "0x%07x" % value["Trigger"],
                                 "%5d" % iBlock,
                                 "    %5d" % value["nWord64"],
                                 "   %4x" % value["magic"],
                             ]))


def oneFedBu(d):
    header = "   ".join(["magic".rjust(12), "nWord64".rjust(15)])
    printer.blue("--wrapper" + ("-" * len(header)))
    printer.blue(header)
    printer.blue("0x%16x   %7d" % (d["magic"], d["nWord64"]))
