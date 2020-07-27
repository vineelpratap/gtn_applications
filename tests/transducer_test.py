import sys

sys.path.append("..")

import gtn
import math
import torch
import unittest

from transducer import Transducer
from utils import CTCLoss
from torch.autograd import gradcheck


class TestTransducer(unittest.TestCase):
    def test_fwd_trivial(self):
        T = 3
        N = 2
        emissions = torch.FloatTensor([1.0, 0.0, 0.0, 1.0, 1.0, 0.0]).view(1, T, N)
        log_probs = torch.log(emissions)

        # Check without blank:
        labels = [[0, 1, 0]]
        transducer = Transducer(tokens=["a", "b"], graphemes_to_idx={"a": 0, "b": 1})
        self.assertAlmostEqual(transducer(log_probs, labels).item(), 0.0)

        # Check with blank:
        labels = [[0, 0]]
        transducer = Transducer(tokens=["a"], graphemes_to_idx={"a": 0}, blank=True)
        self.assertAlmostEqual(transducer(log_probs, labels).item(), 0.0)

        # Check with repeats not allowed:
        labels = [[0, 0]]
        transducer = Transducer(
            tokens=["a"], graphemes_to_idx={"a": 0}, blank=True, allow_repeats=False
        )
        self.assertAlmostEqual(transducer(log_probs, labels).item(), 0.0)

    def test_fwd(self):
        T = 3
        N = 4
        labels = [[1, 2]]
        emissions = torch.FloatTensor([1.0] * T * N).view(1, T, N)
        log_probs = torch.log(emissions)
        log_probs = torch.nn.functional.log_softmax(torch.log(emissions), 2)
        transducer = Transducer(
            tokens=["a", "b", "c"],
            graphemes_to_idx={"a": 0, "b": 1, "c": 2},
            blank=True,
        )
        fwd = transducer(log_probs, labels)
        self.assertAlmostEqual(fwd.item(), -math.log(0.25 * 0.25 * 0.25 * 5))

    def test_ctc(self):
        T = 5
        N = 6

        # Test 1
        labels = [[0, 1, 2, 1, 0]]
        # fmt: off
        emissions = torch.tensor((
            0.633766,  0.221185, 0.0917319, 0.0129757,  0.0142857,  0.0260553,
            0.111121,  0.588392, 0.278779,  0.0055756,  0.00569609, 0.010436,
            0.0357786, 0.633813, 0.321418,  0.00249248, 0.00272882, 0.0037688,
            0.0663296, 0.643849, 0.280111,  0.00283995, 0.0035545,  0.00331533,
            0.458235,  0.396634, 0.123377,  0.00648837, 0.00903441, 0.00623107,
            ),
            requires_grad=True,
        )
        # fmt: on
        log_emissions = torch.log(emissions.view(1, T, N))
        log_emissions.retain_grad()
        transducer = Transducer(
            tokens=["a", "b", "c", "d", "e"],
            graphemes_to_idx={"a": 0, "b": 1, "c": 2, "d": 3, "e": 4},
            blank=True,
        )

        loss = transducer(log_emissions, labels)
        self.assertAlmostEqual(loss.item(), 3.34211, places=4)
        loss.backward(retain_graph=True)
        # fmt: off
        expected_grad = torch.tensor((
            -0.366234, 0.221185,  0.0917319, 0.0129757,  0.0142857,  0.0260553,
            0.111121,  -0.411608, 0.278779,  0.0055756,  0.00569609, 0.010436,
            0.0357786, 0.633813,  -0.678582, 0.00249248, 0.00272882, 0.0037688,
            0.0663296, -0.356151, 0.280111,  0.00283995, 0.0035545,  0.00331533,
            -0.541765, 0.396634,  0.123377,  0.00648837, 0.00903441, 0.00623107,
        )).view(1, T, N)
        # fmt: on
        self.assertTrue(log_emissions.grad.allclose(expected_grad))

        # Test 2
        labels = [[0, 1, 1, 0]]
        # fmt: off
        emissions = torch.tensor((
            0.30176,  0.28562,  0.0831517, 0.0862751, 0.0816851, 0.161508,
            0.24082,  0.397533, 0.0557226, 0.0546814, 0.0557528, 0.19549,
            0.230246, 0.450868, 0.0389607, 0.038309,  0.0391602, 0.202456,
            0.280884, 0.429522, 0.0326593, 0.0339046, 0.0326856, 0.190345,
            0.423286, 0.315517, 0.0338439, 0.0393744, 0.0339315, 0.154046,
            ),
            requires_grad=True,
        )
        # fmt: on
        log_emissions = torch.log(emissions.view(1, T, N))
        log_emissions.retain_grad()
        transducer = Transducer(
            tokens=["a", "b", "c", "d", "e"],
            graphemes_to_idx={"a": 0, "b": 1, "c": 2, "d": 3, "e": 4},
            blank=True,
            allow_repeats=False,
        )
        loss = transducer(log_emissions, labels)
        self.assertAlmostEqual(loss.item(), 5.42262, places=4)
        loss.backward()

        # fmt: off
        expected_grad = torch.tensor((
            -0.69824,  0.28562,   0.0831517, 0.0862751, 0.0816851, 0.161508,
            0.24082,   -0.602467, 0.0557226, 0.0546814, 0.0557528, 0.19549,
            0.230246,  0.450868,  0.0389607, 0.038309,  0.0391602, -0.797544,
            0.280884,  -0.570478, 0.0326593, 0.0339046, 0.0326856, 0.190345,
            -0.576714, 0.315517,  0.0338439, 0.0393744, 0.0339315, 0.154046,
        )).view(1, T, N)
        # fmt: on
        self.assertTrue(log_emissions.grad.allclose(expected_grad))

    def test_simple_decomposition(self):
        T = 5
        tokens = ["a", "b", "ab", "ba", "aba"]
        scores = torch.randn((1, T, len(tokens)), requires_grad=True)
        labels = [[0, 1, 0]]
        transducer = Transducer(tokens=tokens, graphemes_to_idx={"a": 0, "b": 1})

        # Hand construct the alignment graph with all of the decompositions
        alignments = gtn.Graph(False)
        alignments.add_node(True)

        # Add the path ['a', 'b', 'a']
        alignments.add_node()
        alignments.add_arc(0, 1, 0)
        alignments.add_arc(1, 1, 0)
        alignments.add_node()
        alignments.add_arc(1, 2, 1)
        alignments.add_arc(2, 2, 1)
        alignments.add_node(False, True)
        alignments.add_arc(2, 3, 0)
        alignments.add_arc(3, 3, 0)

        # Add the path ['a', 'ba']
        alignments.add_node(False, True)
        alignments.add_arc(1, 4, 3)
        alignments.add_arc(4, 4, 3)

        # Add the path ['ab', 'a']
        alignments.add_node()
        alignments.add_arc(0, 5, 2)
        alignments.add_arc(5, 5, 2)
        alignments.add_arc(5, 3, 0)

        # Add the path ['aba']
        alignments.add_node(False, True)
        alignments.add_arc(0, 6, 4)
        alignments.add_arc(6, 6, 4)

        emissions = gtn.linear_graph(T, len(tokens), True)

        emissions.set_weights(scores.data_ptr())
        expected_loss = gtn.subtract(
            gtn.forward_score(emissions),
            gtn.forward_score(gtn.intersect(emissions, alignments)),
        )

        loss = transducer(scores, labels)
        self.assertAlmostEqual(loss.item(), expected_loss.item(), places=5)
        loss.backward()
        gtn.backward(expected_loss)

        expected_grad = torch.tensor(emissions.grad().weights_to_numpy())
        expected_grad = expected_grad.view((1, T, len(tokens)))
        self.assertTrue(
            torch.allclose(scores.grad, expected_grad, rtol=1e-4, atol=1e-5)
        )

    def test_ctc_compare(self):
        T = 20
        N = 15
        B = 5
        tgt = [
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            [1, 1],
            [0, 2, 3],
            [0, 0, 0, 0, 0],
            [0, 4, 8, 12],
        ]

        tokens = list((t,) for t in range(N - 1))
        graphemes_to_idx = {t: t for t in range(N - 1)}
        inputs = torch.randn(B, T, N, dtype=torch.float, requires_grad=True)

        # With and without target length reduction:
        for reduction in ["none", "mean"]:
            transducer = Transducer(
                tokens=tokens,
                graphemes_to_idx=graphemes_to_idx,
                blank=True,
                allow_repeats=False,
                reduction=reduction,
            )
            ctc_inputs = torch.nn.functional.log_softmax(inputs, 2)
            ctc_result = CTCLoss(ctc_inputs, tgt, N - 1, reduction)
            ctc_result.backward()
            ctc_grad = inputs.grad
            inputs.grad = None

            transducer_result = transducer(inputs, tgt)
            transducer_result.backward()
            transducer_grad = inputs.grad
            inputs.grad = None

            self.assertAlmostEqual(
                ctc_result.item(), transducer_result.item(), places=4
            )
            self.assertTrue(
                torch.allclose(ctc_grad, transducer_grad, rtol=1e-4, atol=1e-5)
            )

    def test_viterbi(self):
        T = 5
        N = 4
        B = 2

        # fmt: off
        emissions1 = torch.tensor((
            0, 4, 0, 1,
            0, 2, 1, 1,
            0, 0, 0, 2,
            0, 0, 0, 2,
            8, 0, 0, 2,
            ),
            dtype=torch.float,
        ).view(T, N)
        emissions2 = torch.tensor((
            0, 2, 1, 7,
            0, 2, 9, 1,
            0, 0, 0, 2,
            0, 0, 5, 2,
            1, 0, 0, 2,
            ),
            dtype=torch.float,
        ).view(T, N)
        # fmt: on

        # Test without blank:
        labels = [[1, 3, 0], [3, 2, 3, 2, 3]]
        transducer = Transducer(
            tokens=["a", "b", "c", "d"],
            graphemes_to_idx={"a": 0, "b": 1, "c": 2, "d": 3},
            blank=False,
        )
        emissions = torch.stack([emissions1, emissions2], dim=0)
        predictions = transducer.viterbi(emissions)
        self.assertEqual([p.tolist() for p in predictions], labels)

        # Test with blank without repeats:
        labels = [[1, 0], [2, 2]]
        transducer = Transducer(
            tokens=["a", "b", "c"],
            graphemes_to_idx={"a": 0, "b": 1, "c": 2},
            blank=True,
            allow_repeats=False,
        )
        emissions = torch.stack([emissions1, emissions2], dim=0)
        predictions = transducer.viterbi(emissions)
        self.assertEqual([p.tolist() for p in predictions], labels)


if __name__ == "__main__":
    unittest.main()