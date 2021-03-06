import transformers
import tensorflow as tf

from model import Classifier
from dataset import get_dataset

# Set some hyper-parameters.
EPOCHS = 5
BATCH_SIZE = 12
MAX_LEN = 512  # The max sequence length that BERT can handle is 512.

# Get the dataset
print('Preparing dataset...')
dataset, n = get_dataset(mode='train', batch_size=BATCH_SIZE)

# Build the BERT model.
model = Classifier()
model(tf.zeros((6, BATCH_SIZE, MAX_LEN), dtype=tf.int32))
model.summary()

# Set up the optimizer and the loss function.
decay_lr_scheduler = tf.keras.optimizers.schedules.PolynomialDecay(
    initial_learning_rate=2e-5,
    decay_steps=10000,
    end_learning_rate=0.0
)
warmup_lr_scheduler = transformers.WarmUp(
    initial_learning_rate=2e-5,
    decay_schedule_fn=decay_lr_scheduler,
    warmup_steps=1000
)
optimizer = tf.keras.optimizers.Adam(learning_rate=warmup_lr_scheduler, clipnorm=1.0)
categorical_cross_entropy_loss = tf.keras.losses.CategoricalCrossentropy()
accuracy = tf.keras.metrics.CategoricalAccuracy()

# Make a checkpoint manager to save the trained model later.
checkpoint = tf.train.Checkpoint(model=model)
manager = tf.train.CheckpointManager(checkpoint, directory='ckpt', checkpoint_name='model.ckpt', max_to_keep=3)


@tf.function
def _train_step(inputs):
    x, y = inputs[:-1], inputs[-1]
    with tf.GradientTape() as tape:
        pred = model(x)
        _loss = categorical_cross_entropy_loss(y, pred)
    grads = tape.gradient(_loss, model.trainable_weights)
    optimizer.apply_gradients(zip(grads, model.trainable_weights))
    accuracy.update_state(y, pred)
    return _loss


for i in range(EPOCHS):
    print(f'Epoch {i + 1}/{EPOCHS}')
    progbar = tf.keras.utils.Progbar(n, stateful_metrics=['loss', 'acc'], unit_name='example')
    for idx, batch in enumerate(dataset):
        loss = _train_step(batch)
        progbar.add(BATCH_SIZE, values=[('loss', loss), ('acc', accuracy.result())])
        accuracy.reset_states()

        # Save a checkpoint every 10 batches.
        if idx % 10 == 0:
            manager.save(checkpoint_number=idx)
