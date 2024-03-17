Ablation Study:

We used mixed precission with nvidia amp in order to speed up the trainig time.
We trained the modelS on Google Colab V100 GPU.
We experimented with both ROBERTA AND BERT models, but found that BERT performs better on this task.
For the BERT model, we used used the bert-large-uncased-whole-word-masking-finetuned-squad pretraied model

The training COLAB: https://colab.research.google.com/drive/1DmIMb5vIHpQJykyfIJCEttlbcknc0cI9#scrollTo=dVwgtkdyixay
The Kaggle submission: https://www.kaggle.com/code/radustefanmihalache/evalnotebook?scriptVersionId=159329245

On the Kaggle submission, we obtained 0.7041 score, which puts us in the 4th place out of 1000+ participants
