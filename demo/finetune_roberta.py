import os
import argparse
from datasets import Dataset
from transformers import RobertaForSequenceClassification, RobertaTokenizerFast, Trainer, TrainingArguments
from transformers import DataCollatorWithPadding
from label_studio_sdk import Client


def fetch_label_studio_data(api_url, api_key, project_id):
    ls = Client(url=api_url, api_key=api_key)
    project = ls.get_project(project_id)
    return project.export_tasks(export_type='JSON_MIN')


def prepare_dataset(label_tasks):
    texts = [task['data']['text'] for task in label_tasks]
    labels = [task['annotations'][0]['result'][0]['value']['labels'][0] for task in label_tasks]
    return {'text': texts, 'label': labels}


def main(args):
    label_tasks = fetch_label_studio_data(args.label_studio_url, args.api_key, args.project_id)
    data_dict = prepare_dataset(label_tasks)
    dataset = Dataset.from_dict(data_dict)

    tokenizer = RobertaTokenizerFast.from_pretrained('roberta-base')
    model = RobertaForSequenceClassification.from_pretrained('roberta-base', num_labels=args.num_labels)
    data_collator = DataCollatorWithPadding(tokenizer)

    def preprocess(example):
        return tokenizer(example['text'], truncation=True)

    tokenized = dataset.map(preprocess, batched=True)

    training_args = TrainingArguments(
        output_dir=os.path.join(args.output_dir, 'roberta-model'),
        evaluation_strategy="epoch",
        num_train_epochs=1,
        per_device_train_batch_size=8,
        save_total_limit=1,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized,
        tokenizer=tokenizer,
        data_collator=data_collator,
    )
    trainer.train()
    trainer.save_model(args.output_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Finetune Roberta with Label Studio data")
    parser.add_argument("--label-studio-url", required=True)
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--project-id", type=int, required=True)
    parser.add_argument("--output-dir", default="./model_out")
    parser.add_argument("--num-labels", type=int, default=2)
    args = parser.parse_args()
    main(args)
