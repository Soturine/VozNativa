"""v0.10 CP7 (V010-GAP-15): plural_agreement false alarms found on edited real text.

The shapes come from triage of UD Portuguese-GSD (test and dev splits, processed locally;
no corpus sentence is copied here). Sentences below are invented, in other domains.
Defect tests fail on v0.9.0; controls (real agreement errors) pass on both.
"""
import unittest

from voznativa.diagnose import diagnose
from voznativa.router import route


def plural_flags(text):
    return [d for d in diagnose(text, route(text, genre="news"))["diagnostics"] if d["type"] == "plural_agreement"]


class PronounDeterminerBeforeVerb(unittest.TestCase):
    def test_defect_pronoun_subject_before_plural_verb(self):
        for text in ("Outras estão em reforma desde o inverno.", "Muitos acharam a feira cara demais.",
                     "Esses foram os melhores tomates da safra.", "Pediu que outros tenham paciência com a fila.",
                     "Muitos aprendem a nadar no rio.", "Todos conhecem a padaria da esquina.",
                     "Poucos fazem pão de fermentação natural.", "A ideia é que todos desliguem as luzes.",
                     "Recebemos cartas, muitas sendo de agradecimento."):
            self.assertEqual(plural_flags(text), [], text)

    def test_defect_clitic_and_adverbs(self):
        for text in ("Eles conhecem os moradores e os ajudam com as compras.",
                     "Só quatro dos cerca de 60 barcos voltaram.", "Chegou às quase onze horas.",
                     "Tocou as então inéditas canções do disco.", "A horta aos poucos foi crescendo."):
            self.assertEqual(plural_flags(text), [], text)

    def test_defect_hyphenated_compound_split_by_spaces(self):
        self.assertEqual(plural_flags("Como muitos rubro - negros esperavam, o time venceu."), [])

    def test_controls_real_agreement_errors_still_flagged(self):
        for text in ("Os resultado da pesquisa mostram melhora.", "Muitos homem chegaram cedo.",
                     "Vários documento sumiram da sala.", "Esses viagem foram longas.",
                     "O lucro veio pelos bom resultados da colheita.", "As norueguesa terminaram em quarto."):
            self.assertEqual(len(plural_flags(text)), 1, text)


if __name__ == "__main__":
    unittest.main()
