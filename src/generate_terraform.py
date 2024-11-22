from dataclasses import dataclass
import re
from pathlib import Path

import pymysql as mysql
from rich import print
import typer
from jinja2 import Environment, FileSystemLoader

app = typer.Typer()

# region Commands
@app.command()
def simple_provider(
    path: str,
    mysql_endpoint: str,
    mysql_username: str,
    mysql_password: str,
    port: int = 3306,
):
    tf_folder = _validate_path(path)

    env = Environment(loader=FileSystemLoader("template"))

    template = env.get_template("simple_provider.jinja.tf")
    output = template.render(
        mysql_endpoint=mysql_endpoint,
        mysql_username=mysql_username,
        mysql_password=mysql_password,
        port=port,
    )
    filename = tf_folder / "providers.tf"
    with open(filename, "w") as f:
        f.write(output)

    _print_output(str(filename), output)


@app.command()
def rds_provider(
    path: str,
    db_instance_id: str,
    db_instance_terraform_id: str,
):
    if not db_instance_terraform_id.isidentifier():
        typer.echo(f"DB_INSTANCE_TERRAFORM_ID must be a valid identifier")
        raise typer.Abort()

    tf_folder = _validate_path(path)
    env = Environment(loader=FileSystemLoader("template"))

    template = env.get_template("rds_provider.jinja.tf")
    output = template.render(
        db_instance_id=db_instance_id,
        db_instance_terraform_id=db_instance_terraform_id,
    )

    filename = tf_folder / "providers.tf"
    with open(filename, "w") as f:
        f.write(output)

    _print_output(str(filename), output)


@app.command()
def data(
    path: str,
    db_instance_name: str,
    db_instance_terraform_id: str,
):
    tf_folder = _validate_path(path)

    env = Environment(loader=FileSystemLoader("template"))
    template = env.get_template("data.jinja.tf")
    output = template.render(
        db_instance_name=db_instance_name,
        db_instance_terraform_id=db_instance_terraform_id,
    )

    filename = tf_folder / "data.tf"
    with open(filename, "w") as f:
        f.write(output)

    _print_output(str(filename), output)

@app.command()
def users(
    path: str,
    mysql_endpoint: str,
    mysql_username: str,
    mysql_password: str,
    port: int = 3306,
):
    tf_folder = _validate_path(path)

    user_grants_list = _get_user_grant_list(
        mysql_endpoint,
        mysql_username,
        mysql_password,
        port,
    )

    env = Environment(loader=FileSystemLoader("template"))
    template = env.get_template("resources.jinja.tf")
    output = template.render(
        user_grants_list=user_grants_list,
    )

# endregion

# region Helpers
def _validate_path(path: str) -> Path:
    tf_folder = Path(path)
    if not tf_folder.exists():
        typer.echo(f"Path '{path}' does not exist")
        raise typer.Abort()
    return tf_folder


def _print_output(filename: str, output: str):
    print(f"[bold]{filename}[/bold]:")
    print(output)
    print("")

@dataclass
class UserGrant:
    database: str
    table: str
    privileges: str
    tls_option: bool
    grant: bool

@dataclass
class UserData:
    user: str
    host: str
    grants: list[UserGrant]

    @property
    def terraform_id(self) -> str:
        identifier = f"{self.user}_{self.host}"
        identifier = re.sub(r'[^a-zA-Z0-9_]', '_', identifier)
        if identifier[0].isdigit():
            identifier = f"_{identifier}"
        return identifier

def _get_user_grant_list(
    host: str,
    username: str,
    password: str,
    port: int = 3306,
) -> list[UserData]:
    grant_pattern = (
        r"GRANT\s+([\w\s,]+)\s+ON\s+([*]|\w+)\.([*]|\w+)\s+TO\s+[`'\w@%]+"
        r"(\s+WITH GRANT OPTION)?(\s+REQUIRE SSL)?"
    )
    result_list: list[UserData] = []
    with mysql.connect(
        host=host,
        user=username,
        password=password,
        port=port,
    ) as conn, conn.cursor() as cursor:
        cursor.execute("SELECT User, Host FROM mysql.user;")
        for user, host in cursor.fetchall():
            cursor.execute(f"SHOW GRANTS FOR '{user}'@'{host}';")
            grants = cursor.fetchall()

            user_data = UserData(
                user=user,
                host=host,
                grants=[],
            )
            for grant in grants:
                match = re.match(
                    grant_pattern,
                    grant[0],
                )
                if match:
                    grants = match.groups(1).replace(", ", "', '") # type: ignore
                    grants = f"['{grants}']"
                    database = str(match.groups(2))
                    table = str(match.groups(3))
                    grant_option = bool(match.groups(4))
                    tls_option = bool(match.groups(5))
                    grant_data = UserGrant(
                        database=database,
                        table=table,
                        privileges=grants,
                        grant=grant_option,
                        tls_option=tls_option,
                    )
                    user_data.grants.append(grant_data)
                else:
                    msg = f"It was not possible to parse the grant: {grant[0]}"
                    raise ValueError(msg)

    return result_list



# endregion

if __name__ == "__main__":
    app()
