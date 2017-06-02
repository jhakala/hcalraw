import collections
from configuration import hw, sw
import printer
from pprint import pprint

def example(raw1={}, raw2={}, book=None, warnQuality=True, fewerHistos=False, **_):
    # sanity check for incoming raw data
    for i, raw in enumerate([raw1, raw2]):
        if not raw:
            continue

        # find the number of time samples in the data
        print "the type of 'raw' is:", type(raw)
        pprint(raw)
        nTsMax = raw[None]["firstNTs"]
        for fedId, d in sorted(raw.iteritems()):
            if fedId is None:
                continue

        # get the important chunks of the raw data
        blocks=d["htrBlocks"].values()

        # sanity checks for these chunks
        for block in blocks:
            if type(block) is not dict:
                printer.warning("FED %d block is not dict" % fedId)
                continue
            elif "channelData" not in block:
                printer.warning("FED %d block has no channelData" % fedId)
                continue


        for channelData in block["channelData"].values():
            if channelData["QIE"]:
                # check the error flags
                errf = "ErrFNZ" if channelData["ErrF"] else "ErrF0"

                # some logic for naming two histograms, one for a clean error flag and another with a problematic error flag
                eq = "!=" if channelData["ErrF"] else "=="

                nAdcMax = 256

                for (i, adc) in enumerate(channelData["QIE"]):
                    if nTsMax <= i:
                        break
                    
                    # fill a 2d histogram where bins on y-axis are ADCs and bins on x-axis are time slice index 
                    book.fill((i, adc), "ADC_vs_TS_%s_%d" % (errf, fedId),
                              (nTsMax, nAdcMax), (-0.5, -0.5), (nTsMax - 0.5, nAdcMax - 0.5),
                              title="FED %d (ErrF %s 0);time slice;ADC;Counts / bin" % (fedId, eq))
