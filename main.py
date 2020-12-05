import argparse
import yaml
import os
import os.path as osp
import torch
from shutil import copyfile
from noise import GenByNoise
from data.data_loader import DataWrapper
import torch.backends.cudnn as cudnn

def get_arguments():
    """Parse all the arguments provided from the CLI.

    Returns:
      A list of parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Generalization by Noise")
    parser.add_argument("--gpu", type=int, nargs='+', default=None, required=True,
                        help="choose gpu device.")
    parser.add_argument("--yaml", type=str, default='config.yaml',
                        help="yaml pathway")
    parser.add_argument("--exp_name", type=str, default='', required=True,
                        help="")
    parser.add_argument("--exp_detail", type=str, default=None, required=False,
                        help="")
    parser.add_argument("--dataset_name", type=str, default=None, required=False,
                        help="")
    parser.add_argument("--model_structure", type=str, default=None, required=True,
                        help="'base', 'GNI', 'advGNI', 'dropout', 'mixup', 'cutmix', 'cutout'")
    parser.add_argument("--data_perturb", type=str, default=None, required=False,
                        help="base, mixup, cutmix, cutout")
    parser.add_argument("--resume", type=str, default=None,
                        required=False, help="")
    parser.add_argument("--resume_mode", type=str, default='adv_attack',
                        required=False, help="normal, gaussian, adv_attack")
    parser.add_argument("--ld", type=float, default=None,
                        required=False, help="Lagrangian Multiplier for L2 penalty")
    parser.add_argument("--num_epochs", type=int, default=None,
                        required=False, help="")

    return parser.parse_args()


def main(config, args):
    """Create the model and start the training."""

    # -------------------------------
    # Setting logging files

    snapshot_dir = config['exp_setting']['snapshot_dir']
    log_dir = config['exp_setting']['log_dir']
    exp_name = args.exp_name

    snapshot_dir, log_dir = os.path.join(snapshot_dir, exp_name), os.path.join(log_dir, exp_name)
    path_list = [snapshot_dir, log_dir]

    for item in path_list:
        if not os.path.exists(item):
            os.makedirs(item)

    config['exp_setting']['snapshot_dir'] = snapshot_dir
    config['exp_setting']['log_dir'] = log_dir

    if args.exp_detail is not None:
        print(args.exp_detail)
        with open(os.path.join(log_dir, 'exp_detail.txt'), 'w') as f:
            f.write(args.exp_detail+'\n')
            f.close()

    # -------------------------------
    # Setting GPU

    gpus_tobe_used = ','.join([str(gpuNum) for gpuNum in args.gpu])
    print('gpus_tobe_used: {}'.format(gpus_tobe_used))
    os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
    os.environ["CUDA_VISIBLE_DEVICES"] = str(gpus_tobe_used)

    cudnn.enabled = True
    cudnn.benchmark = True
    # -------------------------------
    # Setting Test arguments
    if args.dataset_name is not None:
        print('dataset: ', args.dataset_name)
        config['dataset']['name'] = args.dataset_name
    if args.model_structure is not None:
        structure = args.model_structure
        assert structure in config['model']['baseline']
        print('model: ', structure)
        config['model']['baseline'] = structure
    if args.resume is not None:
        checkpoint = torch.load(args.resume)
        mode = args.resume_mode
        print('load {}'.format(args.resume))
    if args.ld is not None:
        print('Lambda: ', args.ld)
        config['train']['ld'][config['dataset']['name']] = args.ld
    if args.num_epochs is not None:
        print('epochs: ', args.num_epochs)
        config['train']['num_epochs'] = args.num_epochs


    with open(os.path.join(log_dir, 'config.yaml'), 'w') as f:
        yaml.dump(config, f)
    # -------------------------------

    dataset = DataWrapper(config)
    solver = GenByNoise(dataset, config)


    if args.resume is None:
        solver.train()
    else:
        solver.test(checkpoint, mode)



if __name__ == '__main__':
    args = get_arguments()
    config = yaml.load(open(args.yaml, 'r'))

    main(config, args)