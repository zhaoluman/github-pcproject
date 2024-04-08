# -*- coding: utf-8 -*-
from config import *
from model import *
from dataset import *

import sys
import torchvision

config = Configuration()
device = torch.device('cuda:{}'.format(config.gpu)) if config.gpu >= 0 else torch.device('cpu')
th_dict = {'ir152':(0.094632, 0.166788, 0.227922), 'irse50':(0.144840, 0.241045, 0.312703),
           'facenet':(0.256587, 0.409131, 0.591191), 'mobile_face':(0.183635, 0.301611, 0.380878)}

def test(model, test_loader, target_name, simi_scores_dict):
    for it, data in enumerate(test_loader):
        # Un-makeup eye area images
        before_img = data[0].to(device).detach()
        # Un-makeup images' path
        before_path = data[2]

        # Save the generated examples with adversarial makeup
        # and save the simi-scores to the "simi_scores_dict"
        model.save_res_img(it, before_img, before_path, simi_scores_dict, target_name)
        model.save_res_tmp_img(it, before_img, before_path, target_name)

def asr_calculation(simi_scores_dict):
    # Iterate each image pair's simi-score from "simi_scores_dict" and compute the attacking success rate
    for key, values in simi_scores_dict.items():
        th01, th001, th0001 = th_dict[key]
        total = len(values)
        success01 = 0
        success001 = 0
        success0001 = 0
        for v in values:
            if v > th01:
                success01 += 1
            if v > th001:
                success001 += 1
            if v > th0001:
                success0001 += 1
        print(key, " attack success(far@0.1) rate: ", success01 / total)
        print(key, " attack success(far@0.01) rate: ", success001 / total)
        print(key, " attack success(far@0.001) rate: ", success0001 / total)

def main():
    simi_scores_dict = {}
    # Calculate the overall simi-scores among all the image pairs
    # and save the results to the "simi_scores_dict"
    for target_name in os.listdir(config.data_dir + '/target_aligned_600')[0:]:
        print(target_name)
        # Initialize the data-loader
        dataset = dataset_makeup(config)
        test_loader = torch.utils.data.DataLoader(dataset, batch_size=1,
                                                  shuffle=False, num_workers=config.n_threads)

        # Initialize the Adv-Makeup
        model = MakeupAttack(config)

        # Pre-trained model loading
        model_id = config.epoch_steps - 1
        model_enc_dict = torch.load(config.model_dir + '/' +
                                    target_name.split('.')[0] + '/%05d_enc.pth' % (model_id))
        model_dec_dict = torch.load(config.model_dir + '/' +
                                    target_name.split('.')[0] + '/%05d_dec.pth' % (model_id))
        model_discr_dict = torch.load(config.model_dir + '/' +
                                      target_name.split('.')[0] + '/%05d_discr.pth' % (model_id))
        # Load the params of pre-trained encoder
        model.enc.load_state_dict(model_enc_dict)
        # Load the params of pre-trained decoder
        model.dec.load_state_dict(model_dec_dict)
        # Load the params of pre-trained discriminator
        model.discr.load_state_dict(model_discr_dict)

        model.eval()

        test(model, test_loader, target_name, simi_scores_dict)


    # Iterate each image pair's simi-score from "simi_scores_dict" and compute the attacking success rate
    asr_calculation(simi_scores_dict)


if __name__ == '__main__':
    main()
