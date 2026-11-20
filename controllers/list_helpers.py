import math

from werkzeug.urls import url_encode

from odoo.http import request
from odoo.osv import expression


PAGE_SIZES = (10, 25, 50, 100)


class TritonListHelpers:
    def _list_page(
        self,
        model,
        domain,
        base_url,
        order_options,
        default_order,
        search_fields=(),
        filter_options=(),
    ):
        args = request.httprequest.args
        try:
            page = max(1, int(args.get("page", 1)))
        except (TypeError, ValueError):
            page = 1
        try:
            page_size = int(args.get("limit", PAGE_SIZES[0]))
        except (TypeError, ValueError):
            page_size = PAGE_SIZES[0]
        if page_size not in PAGE_SIZES:
            page_size = PAGE_SIZES[0]

        search_query = (args.get("q") or "").strip()[:100]
        sort = args.get("sort") or ""
        order = order_options.get(sort, (default_order, ""))[0]
        if search_query and search_fields:
            search_domain = expression.OR(
                [[(field_name, "ilike", search_query)] for field_name in search_fields]
            )
            domain = expression.AND([domain, search_domain])

        total = model.search_count(domain)
        page_count = max(1, math.ceil(total / page_size))
        page = min(page, page_count)
        records = model.search(
            domain,
            order=order,
            limit=page_size,
            offset=(page - 1) * page_size,
        )

        query = {
            key: value
            for key, value in args.to_dict(flat=True).items()
            if key not in {"page", "limit", "q", "sort"}
        }
        if search_query:
            query["q"] = search_query
        if sort in order_options:
            query["sort"] = sort
        query["limit"] = page_size

        def page_url(target):
            return f"{base_url}?{url_encode({**query, 'page': target})}"

        return records, {
            "page": page,
            "page_count": page_count,
            "page_size": page_size,
            "page_sizes": PAGE_SIZES,
            "total": total,
            "start": (page - 1) * page_size + 1 if total else 0,
            "end": min(page * page_size, total),
            "previous": page_url(page - 1) if page > 1 else False,
            "next": page_url(page + 1) if page < page_count else False,
            "search_query": search_query,
            "sort": sort if sort in order_options else "",
            "filters": [
                {"name": key, "value": value}
                for key, value in query.items()
                if key not in {"q", "sort", "limit"}
            ],
            "sort_options": [
                {"value": key, "label": order_and_label[1]}
                for key, order_and_label in order_options.items()
                if key
            ],
            "filter_options": [
                {
                    "name": name,
                    "label": label,
                    "selected": args.get(name, ""),
                    "options": options,
                }
                for name, label, options in filter_options
            ],
            "query_string": url_encode({**query, "page": page}),
        }
