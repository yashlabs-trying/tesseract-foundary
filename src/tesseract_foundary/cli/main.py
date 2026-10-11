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


@cli.group()
def registry():
    pass


@registry.command("list")
@click.pass_context
def list_models(ctx):
    from ..registry import ModelRegistry
    reg = ModelRegistry()
    models = reg.list_models()
    if models:
        click.echo("Registered models:")
        for m in models:
            record = reg.get(m)
            av = record.active_version
            ver_str = av.version if av else "no active version"
            click.echo(f"  {m} ({ver_str})")
    else:
        click.echo("No models registered")


@registry.command("register")
@click.argument("name")
@click.argument("path")
@click.option("--backend", default="default")
@click.option("--precision", default="fp32")
@click.option("--description", default="")
@click.pass_context
def register_model(ctx, name, path, backend, precision, description):
    from ..registry import ModelRegistry
    reg = ModelRegistry()
    v = reg.register(name, path, backend, precision, description)
    click.echo(f"Registered {name} as {v.version}")


@registry.command("activate")
@click.argument("name")
@click.argument("version")
@click.pass_context
def activate_version(ctx, name, version):
    from ..registry import ModelRegistry
    reg = ModelRegistry()
    if reg.activate(name, version):
        click.echo(f"Activated {name}:{version}")
    else:
        click.echo(f"Failed to activate {name}:{version}")


if __name__ == "__main__":
    cli()
