#!/usr/bin/env python

import ROOT as r


def entitle(hSum, skip_rxs):
    if hSum:
        title = []
        if skip_rxs:
            title.append("PPOD RXes" +  ",".join(["%2d/%1d" % (sl, rx) for (cr, sl, rx) in skip_rxs]))

        if not title:
            hSum.SetTitle("all channels")
        else:
            hSum.SetTitle("excluding: %s " % "#semicolon ".join(title))


def histo(fileName="", skip_rxs=[]):
    hSum = None
    f = r.TFile(fileName)
    for cr in [22]:
        for sl in range(1, 13):
            for rx in range(2):
                if (cr, sl, rx) in skip_rxs:
                    continue

                h = f.Get("adc_vs_adc_cr%02d_sl%02d_rx%1d" % (cr, sl, rx))
                if not h:
                    continue

                if hSum is None:
                    hSum = h.Clone("adc_vs_adc")
                    hSum.Reset()
                    hSum.SetDirectory(0)
                hSum.Add(h)

    entitle(hSum, skip_rxs)
    return hSum


def fedString(lst=[]):
    return ",".join(["%d" % i for i in lst])


def draw(h, feds1=[], feds2=[]):
    h.SetStats(False)
    h.Draw("colz")
    h.GetXaxis().SetTitle("ADC (FEDs %s)" % fedString(feds1))
    h.GetYaxis().SetTitle("ADC (FEDs %s)" % fedString(feds2))
    h.GetZaxis().SetTitle("samples / bin")

    for x in ["X", "Y", "Z"]:
        ax = getattr(h, "Get%saxis" % x)()
        ax.SetTitleOffset(1.3)
        #ax.CenterTitle()

    m = 0.15
    r.gPad.SetTopMargin(m)
    r.gPad.SetBottomMargin(m)
    r.gPad.SetLeftMargin(m)
    r.gPad.SetRightMargin(m)
    r.gPad.SetTickx()
    r.gPad.SetTicky()
    r.gPad.SetLogz()


def go(fileName="output/latest.root", exclude=None, feds1=[], feds2=[]):
    r.gROOT.SetBatch(True)

    skip_rxs = [(22,  4, 0),
                (22, 10, 0),
                (22, 11, 0),
                ] if exclude else []

    h = histo(fileName, skip_rxs=skip_rxs)

    if h:
        can = r.TCanvas("canvas", "canvas", 1600, 1600)
        draw(h, feds1=feds1, feds2=feds2)

        yx = r.TF1("yx", "x", h.GetXaxis().GetXmin(), h.GetXaxis().GetXmax())
        yx.SetLineColor(r.kBlack)
        yx.SetLineWidth(1)
        yx.Draw("same")

        leg = r.TLegend(0.2, 0.7, 0.35, 0.85)
        leg.SetBorderSize(0)
        leg.SetFillStyle(0)
        leg.AddEntry(yx, "y = x", "l")
        leg.Draw()

        r.gPad.Update()
        pdf = fileName.replace(".root", "_scatter.pdf")
        if exclude:
            pdf = pdf.replace(".pdf", "_exclude.pdf")
        r.gPad.Print(pdf)
    else:
        print "No histograms matching selection were found (consider swapping --feds1 and --feds2)."


if __name__ == "__main__":
    go()
