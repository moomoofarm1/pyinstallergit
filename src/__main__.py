# ===================== src/__main__.py =====================
import argparse

def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    ft = sub.add_parser("finetune", help="Finetune diarization model")
    ft.add_argument("--epochs", type=int, default=1)
    ft.add_argument("--batch_size", type=int, default=2)
    ft.add_argument("--lr", type=float, default=1e-5)
    ft.add_argument("--output_dir", type=str, default="checkpoints/finetune")
    ft.add_argument("--sample_hours", type=float, default=0.1, help="Approx hours of audio to download")
    ft.add_argument("--model_id", type=str, default="syvai/speaker-diarization-3.1", help="Base model ID")

    al = sub.add_parser("active-learn", help="Active learning loop using Label Studio")
    al.add_argument("--iterations", type=int, default=3)
    al.add_argument("--query_k", type=int, default=5)
    al.add_argument("--output_dir", type=str, default="checkpoints/active_learning")
    al.add_argument("--batch_size", type=int, default=2)
    al.add_argument("--lr", type=float, default=1e-5)
    al.add_argument("--ft_epochs", type=int, default=1, help="Fine-tune epochs per iteration")
    al.add_argument("--ls_url", type=str, default="http://localhost:8080", help="Label Studio base URL")
    al.add_argument("--ls_token", type=str, default=None, help="Label Studio API token")
    al.add_argument("--project_id", type=int, default=None, help="Label Studio project ID")
    al.add_argument("--model_id", type=str, default="syvai/speaker-diarization-3.1", help="Base model ID")

    args = p.parse_args()
    if args.cmd == "finetune":
        from finetune_diarization import run_finetune

        run_finetune(
            epochs=args.epochs,
            batch_size=args.batch_size,
            lr=args.lr,
            output_dir=args.output_dir,
            sample_hours=args.sample_hours,
            model_id=args.model_id,
        )
    else:
        from active_learning_diarization import run_active_learning

        run_active_learning(
            iterations=args.iterations,
            query_k=args.query_k,
            output_dir=args.output_dir,
            batch_size=args.batch_size,
            lr=args.lr,
            fine_tune_epochs=args.ft_epochs,
            ls_url=args.ls_url,
            ls_token=args.ls_token,
            project_id=args.project_id,
            model_id=args.model_id,
        )

if __name__ == "__main__":
    main()
