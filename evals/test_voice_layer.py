"""Voice Profile v2, Voice Contract precedence and drift against a profile."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa.contract import compact, resolve
from voznativa.drift import inspect as drift
from voznativa.profile import build, confidence, validate
from voznativa.router import route

DOCS = [
    "O comando lê dois arquivos e devolve um relatório. Ele não reescreve nada; só aponta onde o significado "
    "pode ter mudado. Quando o resultado é fail, a candidata deve ser descartada. Quando é review, alguém precisa olhar.",
    "Para instalar, rode o pip no diretório do projeto. Depois disso, a CLI fica disponível no terminal. Se der "
    "erro de encoding no Windows, passe o caminho do arquivo em vez de usar o pipe; o PowerShell antigo troca "
    "acentos por interrogação antes de o texto chegar ao programa.",
    "O ledger guarda os valores protegidos de cada frase. Números, datas e caminhos entram com uma chave "
    "normalizada, então dois formatos do mesmo valor contam como um só. Isso evita falso vermelho sem esconder "
    "uma troca de valor, que continua reprovando a candidata.",
    "O router decide o gênero só quando a evidência é clara. Se o texto é curto ou ambíguo, ele responde unknown "
    "e o seletor carrega apenas as referências genéricas. Errar por cautela custa pouco; errar de gênero "
    "carrega a regra errada e piora a reescrita.",
]
CHAT = ["vc viu o deploy? nn subiu ainda kkk", "blz, mando amanhã pq hj tá corrido"]


def docs_profile():
    return build([{"text": t, "channel": "github_docs"} for t in DOCS])


class Profile(unittest.TestCase):
    def test_profile_stores_no_raw_text_or_topic_words(self):
        profile = docs_profile()
        dump = json.dumps(profile, ensure_ascii=False)
        for sample in DOCS:
            self.assertNotIn(sample[:40], dump)
        self.assertNotIn("ledger", dump)  # topic word of a sample
        self.assertEqual(profile["lexicon"]["recurring"], [])
        self.assertFalse(profile["privacy"]["retain_raw_samples"])
        self.assertEqual(validate(profile), [])

    def test_confidence_is_capped_by_sample_count(self):
        self.assertEqual(confidence(1, 1), 0.5)
        self.assertEqual(confidence(3, 3), 0.75)
        self.assertLess(confidence(1, 3), confidence(3, 3))

    def test_short_evidence_is_explicit_only(self):
        self.assertEqual(build([{"text": t} for t in CHAT])["maturity"], "explicit_only")
        self.assertEqual(docs_profile()["maturity"], "provisional")

    def test_identity_inference_is_forbidden(self):
        profile = docs_profile()
        profile["inference_policy"]["infer_identity"] = True
        self.assertTrue(validate(profile))

    def test_requires_samples(self):
        with self.assertRaises(ValueError):
            build([])


class ContractPrecedence(unittest.TestCase):
    def context(self, **kwargs):
        return route("O teste falhou.", **kwargs)

    def test_author_channel_profile_beats_genre_preferences(self):
        contract = resolve(self.context(genre="documentation", channel="github_docs"), docs_profile())
        self.assertTrue(contract["features"]["em_dash"]["source"].startswith("author_channel_profile"))

    def test_explicit_instruction_beats_author(self):
        contract = resolve(self.context(genre="documentation", channel="github_docs"), docs_profile(),
                           {"sentence_rhythm": "long"})
        self.assertEqual(contract["features"]["sentence_rhythm"]["value"], "long")
        self.assertEqual(contract["features"]["sentence_rhythm"]["source"], "explicit_instruction")

    def test_mandatory_constraint_beats_explicit_instruction(self):
        contract = resolve(self.context(genre="legal"), None, {"slang_strength": 0.6})
        self.assertEqual(contract["conflicts"][0]["constraint"], "no_slang")
        self.assertEqual(contract["slang_strength"], {"requested": 0.6, "effective": 0.0})

    def test_weak_evidence_follows_source(self):
        weak = build([{"text": t, "channel": "whatsapp"} for t in CHAT])
        contract = resolve(self.context(genre="whatsapp", channel="whatsapp"), weak)
        self.assertEqual(contract["features"]["abbreviations"]["value"], "follow_source")
        self.assertFalse(contract["profile"]["used"])

    def test_regional_strength_is_never_applied_without_evidence(self):
        contract = resolve(self.context(genre="corporate", region="MG", region_strength=0.4))
        self.assertEqual(contract["regional_strength"]["effective"], 0.0)
        self.assertTrue(any("regional" in w for w in contract["warnings"]))

    def test_compact_view_and_do_not_list(self):
        contract = resolve(self.context(genre="technical"))
        view = compact(contract)
        self.assertEqual(view["regional_strength"], 0.0)
        self.assertIn("preserve_code_verbatim", view["constraints"])
        self.assertTrue(any("invent" in rule for rule in contract["do_not"]))


class VoiceMatchInEngine(unittest.TestCase):
    def test_engine_reports_distance_to_the_author_profile(self):
        from voznativa.engine import rewrite
        from voznativa.providers import StaticProvider
        source = ("Prezados, é importante destacar que estaremos realizando a atualização do sistema "
                  "na próxima semana, conforme alinhado anteriormente com todas as áreas envolvidas.")
        closer = "<final>" + DOCS[1] + "</final>"
        result = rewrite(source, route(source, genre="documentation", channel="github_docs"),
                         StaticProvider([closer]), profile=docs_profile(), attempts=1)
        voice = result["quality"]["voice"]
        self.assertIn("original_distance", voice)
        self.assertIn("candidate_distance", voice)
        self.assertIsInstance(voice["moved_toward_profile"], bool)

    def test_long_rewrites_report_drift_between_windows(self):
        from voznativa.engine import rewrite
        from voznativa.providers import StaticProvider
        long_text = "\n\n".join(DOCS * 2)
        source = "É importante destacar que " + long_text
        result = rewrite(source, route(source, genre="documentation"), StaticProvider(["<final>" + long_text + "</final>"]),
                         attempts=1)
        self.assertGreaterEqual(result["quality"]["long_text_drift"]["windows"], 2)


class DriftAgainstProfile(unittest.TestCase):
    def test_same_author_style_does_not_drift(self):
        result = drift("\n\n".join(DOCS[:2]), profile=docs_profile())
        self.assertEqual(result["reference"], "voice_profile")
        self.assertFalse(result["drift"], result["windows"])

    def test_different_style_drifts(self):
        chat = "vc viu?? nn deu certo kkk!! pq será?? manda msg!! tô esperando!! " * 4
        self.assertTrue(drift(chat, profile=docs_profile())["drift"])


if __name__ == "__main__":
    unittest.main()
