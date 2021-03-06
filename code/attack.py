import os
import sys

import pandas as pd

from adversarial import AdversarialAlignments
from adversarial import AdversarialWordLevel
from adversarial import Pacifist
from utils import load_config


def main(config_path: str = 'config.yaml'):
    config = load_config(config_path)

    languages = config['languages']

    pacifist = Pacifist(config_path=config_path)
    word_level_attacker = AdversarialWordLevel(config_path=config_path)
    alignments_attacker = AdversarialAlignments(config_path=config_path)

    word_level_attacker.num_examples = config['num_examples']
    alignments_attacker.num_examples = config['num_examples']

    model_name = f'{config["model_name"]}_{int(config["only_english"])}_{int(config["load_adv_pretrained"])}.csv'

    try:
        print('Test set')

        results = {}
        pacifist.port_model()

        for base_language in languages:
            pacifist.change_base_language(base_language)
            results[base_language] = pacifist.attack_dataset()

        pacifist.port_model()

        if not os.path.exists('results/test/'):
            os.mkdir('results/test/')

        pd.DataFrame.from_dict(results).transpose().to_csv('results/test/' + model_name)

        base_language = 'en'

        pacifist.change_base_language(base_language)
        word_level_attacker.change_base_language(base_language)
        alignments_attacker.change_base_language(base_language)

        base_path = f'results/{base_language}/'

        if not os.path.exists(base_path):
            os.mkdir(base_path)

        other_languages = list(languages)
        other_languages.remove(base_language)

        pacifist.port_model()

        results = {
            'No attack': pacifist.attack_dataset(),
        }

        pacifist.port_model('cpu')

        # WORD LEVEL

        print('Word level')

        word_level_attacker.port_model()

        for language in other_languages:
            word_level_attacker.change_attack_language(language)
            results[f'Word level [{language}]'] = word_level_attacker.attack_dataset()

        word_level_attacker.port_model('cpu')

        # ALIGNMENTS

        print('Alignments')

        alignments_attacker.port_model()

        for language in other_languages:
            alignments_attacker.change_attack_language(language)
            results[f'Alignments [{language}]'] = alignments_attacker.attack_dataset()

        alignments_attacker.port_model('cpu')

        pd.DataFrame.from_dict(results).transpose().to_csv(base_path + model_name)
    except KeyboardInterrupt:
        try:
            pd.DataFrame.from_dict(results).transpose().to_csv(base_path + model_name)
        finally:
            exit(0)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        main(sys.argv[-1])
    else:
        main()
