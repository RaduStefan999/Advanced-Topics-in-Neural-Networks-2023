from torch import Tensor
from layer import Layer
from benchmarkers import accuracy, cross_entropy_loss


def feed_forward_train(input_data: Tensor, network: [Layer]) -> list[Tensor]:
    output_per_layer = [input_data]
    for layer in network:
        input_data = layer.feed_forward(input_data)
        output_per_layer.append(input_data)
    return output_per_layer


def feed_forward(input_data: Tensor, network: [Layer]) -> Tensor:
    for layer in network:
        input_data = layer.feed_forward(input_data)
    return input_data


def backprop(input_data: Tensor, target: Tensor, learning_rate: float, network: [Layer]):
    nn_outputs = feed_forward_train(input_data, network)
    assert len(nn_outputs) + 1 == len(network)

    error = Layer.compute_error_output_layer(nn_outputs[-1], target)
    for it in range(2, len(network)):

        last_error = Layer.compute_error(nn_outputs[-it], error, network[-it + 1])

        network[-it + 1].weights -= nn_outputs[-it] @ last_error
        network[-it + 1].weights -= last_error

        error = last_error

    last_error = Layer.compute_error(nn_outputs[0], error, network[0])

    network[0].weights -= nn_outputs[0] @ last_error
    network[0].weights -= last_error


def minibatch_train(input_data: Tensor, target: Tensor, learning_rate: float, batch_size: int, network: [Layer]):
    for it in range(len(input_data) // batch_size):
        input_data_for_batch = input_data[(it * batch_size):((it + 1) * batch_size)]
        target_for_batch = target[(it * batch_size):((it + 1) * batch_size)]

        backprop(input_data_for_batch, target_for_batch, learning_rate, network)


def epoch_train(train_set: tuple[Tensor, Tensor],
                validation_set: tuple[Tensor, Tensor],
                learning_rate: float, batch_size: int, nr_of_epochs: int, network: [Layer]):

    train_data, train_target = train_set
    validation_data, validation_target = validation_set

    for epoch in range(nr_of_epochs):
        minibatch_train(train_data, train_target, learning_rate, batch_size, network)

        print(f"TRAINING SET - Accuracy on epoch {epoch} is: {accuracy(train_data, train_target, network)}")
        print(f"TRAINING SET - Loss on epoch {epoch} is: {cross_entropy_loss(train_data, train_target, network)}")

        print(f"VALIDATION SET - Accuracy on epoch {epoch} is: {accuracy(validation_data, validation_target, network)}")
        print(f"VALIDATION SET - Loss on epoch {epoch} is: {cross_entropy_loss(validation_data, validation_target, network)}")

