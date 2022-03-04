import os

from knn_classifier import Classifier


def start_and_end_slot(sub_dir_name) -> (int, int):
    start_slot = int(sub_dir_name.split("_")[1])
    end_slot = int(sub_dir_name.split("_")[3])
    return (start_slot, end_slot)


# List of classifiers
#
# [(start_slot, end_slot, classifier)]
class MultiClassifier:
    def __init__(self, data_dir):
        classifiers = []
        for sub_dir_name in os.listdir(data_dir):
            sub_dir_path = os.path.join(data_dir, sub_dir_name)

            start_slot, end_slot = start_and_end_slot(sub_dir_name)

            print(f"loading classifier for range {start_slot}..={end_slot}")

            classifier = Classifier(sub_dir_path)

            classifiers.append((start_slot, end_slot, classifier))

        self.classifiers = sorted(classifiers, key=lambda x: x[0])

    def classify(self, block_reward):
        slot = int(block_reward["meta"]["slot"])

        for (i, (start_slot, end_slot, classifier)) in enumerate(self.classifiers):
            # Allow the last classifier to be used for slots beyond its end slot
            if start_slot <= slot and (
                slot <= end_slot or i + 1 == len(self.classifiers)
            ):
                return classifier.classify(block_reward)

        raise Exception(f"no classifier known for slot {slot}")

    def scores(self):
        return [
            (start, end, classifier.score)
            for (start, end, classifier) in self.classifiers
        ]
