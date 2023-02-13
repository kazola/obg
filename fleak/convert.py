from mat.data_converter import default_parameters, DataConverter


def cnv():
    f = '/home/kaz/Downloads/dl_fleak/60-77-71-22-C9-B3/1000000_fle_20230213_024244.lid'
    parameters = default_parameters()
    DataConverter(f, parameters).convert()


if __name__ == '__main__':
    cnv()
