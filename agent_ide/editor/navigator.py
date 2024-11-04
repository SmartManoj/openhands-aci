from collections import defaultdict
from pathlib import Path

from tqdm import tqdm

from agent_ide.tree_sitter.parser import TagKind, TreeSitterParser
from agent_ide.utils.file import GitRepoUtils
from agent_ide.utils.path import PathUtils


class SymbolNavigator:
    def __init__(self, root='./', show_progress=False) -> None:
        if not Path(root).is_absolute():
            root = str(Path(root).resolve())

        self.root = root
        self.show_progress = show_progress

        self.git_utils = GitRepoUtils(self.root)
        self.path_utils = PathUtils(self.root)
        self.ts_parser = TreeSitterParser(self.root)

    def get_parsed_tags(
        self,
        depth: int | None = None,
        rel_dir_path: str | None = None,
    ) -> tuple[dict, dict, dict, dict]:
        if rel_dir_path:
            all_abs_files = self.git_utils.get_absolute_tracked_files_in_directory(
                rel_dir_path=rel_dir_path,
                depth=depth,
            )
        else:
            all_abs_files = self.git_utils.get_all_absolute_tracked_files(depth=depth)

        ident2defrels = defaultdict(
            set
        )  # symbol identifier -> set of its definitions' relative file paths
        ident2refrels = defaultdict(
            list
        )  # symbol identifier -> list of its references' relative file paths
        identwrel2deftags = defaultdict(
            set
        )  # (relative file, symbol identifier) -> set of its DEF tags
        identwrel2reftags = defaultdict(
            set
        )  # (relative file, symbol identifier) -> set of its REF tags

        all_abs_files_iter = (
            tqdm(all_abs_files, desc='Parsing tags', unit='file')
            if self.show_progress
            else all_abs_files
        )
        for abs_file in all_abs_files_iter:
            rel_file = self.path_utils.get_relative_path_str(abs_file)
            parsed_tags = self.ts_parser.get_tags_from_file(abs_file, rel_file)

            for parsed_tag in parsed_tags:
                if parsed_tag.tag_kind == TagKind.DEF:
                    ident2defrels[parsed_tag.node_name].add(rel_file)
                    identwrel2deftags[(rel_file, parsed_tag.node_name)].add(parsed_tag)
                if parsed_tag.tag_kind == TagKind.REF:
                    ident2refrels[parsed_tag.node_name].append(rel_file)
                    identwrel2reftags[(rel_file, parsed_tag.node_name)].add(parsed_tag)

        return ident2defrels, ident2refrels, identwrel2deftags, identwrel2reftags
