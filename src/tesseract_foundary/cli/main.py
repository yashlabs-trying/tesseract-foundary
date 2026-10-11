import click
from ..config import load_config
from ..utils.logger import get_logger


@click.group()
@click.option("--config", "-c", default="config.yaml", help="Config file path")
@click.pass_context
def cli(ctx, config):
    cfg = load_config(config)
    ctx.ensure_object(dict)
    ctx.obj["config"] = cfg
    ctx.obj["logger"] = get_logger("tesseract-foundry", cfg.logging.level)


@cli.command()
@click.pass_context
def serve(ctx):
    logger = ctx.obj["logger"]
    config = ctx.obj["config"]
    logger.info(f"Starting Tesseract Foundry v{config.version}")
    logger.info(f"Server: {config.server.host}:{config.server.port}")
    from ..api.server import Server
    server = Server(config)
    server.start()


@cli.command()
@click.pass_context
def version(ctx):
    config = ctx.obj["config"]
    click.echo(f"Tesseract Foundry v{config.version}")


if __name__ == "__main__":
    cli()
