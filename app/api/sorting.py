from enum import StrEnum
from typing import Dict


class SortOption(StrEnum):
    RELEVANCE = "relevance"
    VIEWS = "views"
    RECENT = "recent"


def get_search_query(sort_option: str) -> str:
    if sort_option == SortOption.VIEWS:
        return """
            WITH matches AS (
                SELECT rowid, vec_distance_cosine(embedding, :embedding) as distance
                FROM vector_source
                ORDER BY distance
                LIMIT :top_n
            )
            SELECT ideas.*, matches.distance AS distance
            FROM matches
            LEFT JOIN ideas ON ideas.rowid = matches.rowid
            LEFT JOIN youtube ON ideas.video_id = youtube.video_id
            ORDER BY youtube.views DESC
            LIMIT :page_size OFFSET :offset
        """
    elif sort_option == SortOption.RECENT:
        return """
            WITH matches AS (
                SELECT rowid, vec_distance_cosine(embedding, :embedding) as distance
                FROM vector_source
                ORDER BY distance
                LIMIT :top_n
            )
            SELECT ideas.*, matches.distance AS distance
            FROM matches
            LEFT JOIN ideas ON ideas.rowid = matches.rowid
            LEFT JOIN youtube ON ideas.video_id = youtube.video_id
            ORDER BY youtube.publish_date DESC
            LIMIT :page_size OFFSET :offset
        """
    else:
        return """
            WITH matches AS (
                SELECT rowid, vec_distance_cosine(embedding, :embedding) as distance
                FROM vector_source
                ORDER BY distance
            )
            SELECT ideas.*, matches.distance AS distance
            FROM matches
            LEFT JOIN ideas ON ideas.rowid = matches.rowid
            ORDER BY distance
            LIMIT :page_size OFFSET :offset
        """


def get_sort_display_name(sort_option: str) -> str:
    mapping = {
        SortOption.RELEVANCE: "Relevance",
        SortOption.VIEWS: "Most Viewed",
        SortOption.RECENT: "Most Recent",
    }
    return mapping.get(sort_option, "Relevance")
