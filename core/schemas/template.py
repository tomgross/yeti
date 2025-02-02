import os
from typing import ClassVar

import jinja2
from pydantic import BaseModel

from core import database_arango

# TODO: Import Jinja functions to render templates


class Template(BaseModel, database_arango.ArangoYetiConnector):
    """A template for exporting data to an external system."""

    _collection_name: ClassVar[str] = "templates"

    id: str | None = None
    name: str
    template: str

    @classmethod
    def load(cls, object: dict) -> "Template":
        return cls(**object)

    def render(self, data: list["Observable"], output_file: str | None) -> None | str:
        """Renders the template with the given data to the output file."""

        environment = jinja2.Environment()
        template = environment.from_string(self.template)
        result = template.render(data=data)
        if output_file:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, "w+") as fd:
                fd.write(result)
        else:
            return result
