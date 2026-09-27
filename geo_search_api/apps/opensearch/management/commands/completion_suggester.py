import time
import typing

from django.core.management.base import BaseCommand, CommandError
from clients import opensearch


class Command(BaseCommand):
    help = "Prepare hte indexes to work with the completion suggester."

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)
        self._index = None
        self._opensearch = opensearch.OpenSearchClient()

    def add_arguments(self, parser):
        """
        Add the command options
        """
        # Positional arguments
        parser.add_argument(
            "action",
            type=str,
            help="Define the action which need to apply to the index. Allowed values: rebuild",
        )
        # Named arguments
        parser.add_argument(
            "--index",
            required=True,
            type=str,
            help=(
                "Option to define the name of index to which need to apply the action. Allowed "
                "values: basin-shape-index, wells_ontology, document_location, las_files"
            ),
            choices=(
                "basin-shape-index",
                "wells_ontology",
                "document_location",
                "las_files",
            ),
        )

    def handle(self, *args, **options):
        """
        Command handler
        """
        self._index = options.get("index")
        try:
            getattr(self, options["action"])()
        except AttributeError:
            self._write_error("Wrong action value. Available values: rebuild")

    def rebuild(self):

        self.stdout.write("REBUILD:")
        self.stdout.write(f" > Index: {self._index}")
        _, response = self._opensearch.count(
            index_name=self._index, query_type=opensearch.QueryTypeEnum.MATCH_ALL
        )
        number_of_documents_at_the_begin = response.get("count")
        self.stdout.write("   Total number of documents: " + str(number_of_documents_at_the_begin))

        try:
            result = getattr(self, "_rebuild_" + self._index.replace("-", "_"))(
                number_of_documents_at_the_begin=number_of_documents_at_the_begin
            )

            if result is not None:
                self.stdout.write(
                    " > Total number of documents in the rebuild index ...", ending=""
                )
                number_of_documents_at_the_end = 0
                while number_of_documents_at_the_end < number_of_documents_at_the_begin:
                    _, response = self._opensearch.count(
                        index_name=self._index, query_type=opensearch.QueryTypeEnum.MATCH_ALL
                    )
                    number_of_documents_at_the_end = response.get("count")
                    self.stdout.write(".", ending="")
                    time.sleep(1)

                self.stdout.write(" " + str(number_of_documents_at_the_end))
                self._write_success()

        except AttributeError:
            self._write_error(
                f" > The action rebuild does not supported for the index {self._index}"
            )

    def _rebuild_basin_shape_index(self, **kwargs):
        self._rebuild_scenario_a(properties_to_rebuild=["Name"])
        return True

    def _rebuild_wells_ontology(self, **kwargs):
        self._rebuild_scenario_a(properties_to_rebuild=["well_name", "uwi", "operator", "region"])
        return True

    def _rebuild_las_files(self, **kwargs):
        self._rebuild_scenario_b(**kwargs)
        return True

    def _rebuild_document_location(self, **kwargs):
        self._rebuild_scenario_a(properties_to_rebuild=["country"])
        self._rebuild_scenario_b(**kwargs)
        return True

    def _write_success(self, message: str = "SUCCESS"):
        """
        Write the message with `success` style
        """
        self.stdout.write(self.style.SUCCESS(message))

    def _write_error(self, message: str):
        """
        Write the message with `error` style
        """
        self.stdout.write(self.style.ERROR(message))

    def _execute_opensearch_command(self, command: typing.Callable, **kwargs):

        write_ok = kwargs.pop("write_ok", True)
        okay, _ = command(**kwargs)
        if okay:
            if write_ok:
                self._write_success("OK")
            return _
        else:
            self._write_error(_)
            raise CommandError()

    def _rebuild_scenario_a(
        self,
        properties_to_rebuild: typing.List[str],
        force_rebuild: bool = False,
    ):

        okay, _index_settings = self._opensearch.get_index(index_name=self._index)
        if not okay:
            self._write_error(f" > Failed: {_index_settings}")
            return
        # We remove unnecessary settings.
        for key_to_delete in ["creation_date", "uuid", "version", "provided_name"]:
            del _index_settings["settings"]["index"][key_to_delete]

        need_to_rebuild = force_rebuild
        for _ in properties_to_rebuild:
            if _index_settings.get("mappings").get("properties").get(_).get("type") != "completion":
                _index_settings["mappings"]["properties"][_]["type"] = "completion"
                need_to_rebuild = True

        if not need_to_rebuild:
            self._write_success(
                f" > The index {self._index} is already rebuild and redy to use with the "
                f"completion suggester."
            )
            return

        try:
            self.stdout.write(" > Update index settings ... ", ending="")
            self._execute_opensearch_command(
                self._opensearch.update_settings,
                index_name=self._index,
                settings={"index.blocks.write": True},
            )
            self.stdout.write(f" > Clone index {self._index} to temp_{self._index} ... ", ending="")
            self._execute_opensearch_command(
                self._opensearch.clone_index,
                source_index_name=self._index,
                target_index_name=f"temp_{self._index}",
            )
            self.stdout.write(" > Delete the source index ... ", ending="")
            self._execute_opensearch_command(self._opensearch.delete_index, index_name=self._index)
            self.stdout.write(
                f" > Re-create the index {self._index} with updated settings ... ", ending=""
            )
            self._execute_opensearch_command(
                self._opensearch.create_index,
                index_name=self._index,
                index_settings=_index_settings,
            )
            self.stdout.write(" > Copy documents the updated index ... ", ending="")
            self._execute_opensearch_command(
                self._opensearch.reindex,
                source_index_name=f"temp_{self._index}",
                target_index_name=self._index,
            )
            self.stdout.write(" > Delete the temporary index ... ", ending="")
            self._execute_opensearch_command(
                self._opensearch.delete_index, index_name=f"temp_{self._index}"
            )
        except CommandError:
            self._write_error("FAILED")

        return True

    def _rebuild_scenario_b(self, number_of_documents_at_the_begin: int = 0):

        okay, _index_settings = self._opensearch.get_index(index_name=self._index)
        if not okay:
            self._write_error(f" > Failed: {_index_settings}")
            return

        if "document_name" in _index_settings["mappings"]["properties"]:
            self._write_success(
                f" > The index {self._index} is already rebuild and redy to use with the "
                f"completion suggester"
            )
            return

        # Add a new property `document_name` of the type of `completion`
        self.stdout.write(" > Add a new field document_name ... ", ending="")
        self._execute_opensearch_command(
            self._opensearch.update_mapping,
            index_name=self._index,
            mapping={
                "properties": {
                    "document_name": {
                        **_index_settings["mappings"]["properties"]["document_path"],
                        "type": "completion",
                    }
                }
            },
        )
        self.stdout.write(" > Update the existing documents ...", ending="")
        updated_documents = 0
        while updated_documents < number_of_documents_at_the_begin:
            response = self._execute_opensearch_command(
                self._opensearch.update_by_query,
                index_name=self._index,
                painless_script=(
                    "String path = ctx._source.document_path; "
                    "ctx._source.document_name=path.substring(path.lastIndexOf('/')+1)"
                ),
                query_type=opensearch.QueryTypeEnum.MATCH_ALL,
                write_ok=False,
            )
            updated_documents = response.get("updated")
            time.sleep(1)

        self.stdout.write(f" {updated_documents}")
        return True
