import json
import falcon

from knn_classifier import Classifier as KNNClassifier

DATA_DIR = "./training_data_proc"

class Classifier:
    def __init__(self, datadir):
        print("Initialising classifier, this could take a moment...")
        classifier = KNNClassifier(datadir)
        print(f"Start-up complete, classifier score is {classifier.score}")
        self.classifier = classifier

    def on_post(self, req, resp):
        try:
            block_rewards = json.load(req.bounded_stream)
        except json.decoder.JSONDecodeError as e:
            resp.text = json.dumps({"error": f"invalid JSON: {e}"})
            resp.code = falcon.HTTP_400
            return

        if type(block_rewards) != list:
            resp.text = json.dumps({"error": "/classify accepts a list of block rewards"})
            resp.code = falcon.HTTP_400
            return

        results = []

        for block_reward in block_rewards:
            # Check required fields
            if ("block_root" not in block_reward or
                "attestation_rewards" not in block_reward or
                "per_attestation_rewards" not in block_reward["attestation_rewards"]):
               resp.text = json.dumps({"error": "input JSON is not a block reward"})
               resp.code = falcon.HTTP_400
               return

            best_guess_single, best_guess_multi, probability_map = self.classifier.classify(block_reward)

            results.append({
                "block_root": block_reward["block_root"],
                "best_guess_single": best_guess_single,
                "best_guess_multi": best_guess_multi,
                "probability_map": probability_map,
            })

        resp.text = json.dumps(results, ensure_ascii=False)

app = application = falcon.App()

classifier = Classifier(DATA_DIR)

app.add_route("/classify", classifier)
