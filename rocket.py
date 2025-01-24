#!/usr/bin/env python3

import click


@click.group()
def cli():
    """CLI interface to manage GCS software initialisation"""
    pass


@click.command()
@click.argument('mode')
def run(mode):
    """Start software based on the [mode] argument"""
    mode = mode.lower()

    if mode == 'dev':
        click.echo("Running in containerised dev mode")
    elif mode == 'prod':
        click.echo("Running in production mode")
        raise NotImplementedError("Production setup not currently supported")
    else:
        click.echo(
            f"Invalid mode: {mode}. Please run 'rocket --help' for more information.", err=True)
        exit(1)


# Use groups for nested positional arugments `rocket run dev/prod`
cli.add_command(run)

if __name__ == '__main__':
    cli()
