iws_1 = 65#fhsdgyajikuhy!
iws_2 = 91#asgdtaysudjiyt!!!
iws_3 = 97#asdtgyhjgytyujk!!!!!!!!
iws_4 = 123#danger danger danger don't read
iws_5 = 48#no no no pls uysgfydghfuefygy don't look to the side;;;asuygdsyuhjfwfytu
iws_6 = 58#you're in trouble;;;fsygfajdfsifuyg
iws = [chr(iws) for iws in range(iws_1, iws_2)]
iwss = [chr(iws) for iws in range(iws_3, iws_4)]
wuf = [chr(wuf) for wuf in range(iws_5, iws_6)]
happy = "AmppsaJpex"
sad = "gvego804"

def iwsuff(tx):
    wufwuff = ""#Be gone, snitch!
    for xx in tx:
        if xx in iws:
            tp = iws
        elif xx in iwss:
            tp = iwss
        else:
            tp = wuf
                
        cin = (tp.index(xx) - 4) % len(tp)
        wufwuff += tp[cin]    
    
    return wufwuff
