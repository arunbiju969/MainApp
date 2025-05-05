import os
import json
import re
from django.shortcuts import render, redirect
from django.http import Http404
from django.utils.safestring import mark_safe
from django.urls import reverse
from urllib.parse import unquote


def return_status(request):
    data_dir = os.path.join(os.path.dirname(__file__), "..", "comparellm", "data")
    # List all JSON files that match the pattern
    run_files = [
        f
        for f in os.listdir(data_dir)
        if f.startswith("llm_comparison_results_") and f.endswith(".json")
    ]

    run_choices = []
    for f in run_files:
        match = re.search(r"_run(\d+)\.json$", f)
        run_number = int(match.group(1)) if match else 0
        run_choices.append((f, run_number))

    # Sort by run_number
    run_choices = sorted(run_choices, key=lambda x: x[1])

    selected_run = request.GET.get("run", run_files[0] if run_files else "")

    results_file = os.path.join(data_dir, selected_run)
    with open(results_file, "r", encoding="utf-8") as f:
        results = json.load(f)
    if isinstance(results, dict) and "run_1" in results:
        results = results["run_1"]

    first_query = next(iter(results.values()))
    model_list = list(first_query["model_responses"].keys())

    # Extract providers from model names
    providers = sorted(
        set(m.split("/")[1] for m in model_list if len(m.split("/")) > 1)
    )

    # Get selected provider and model from GET params
    selected_provider = request.GET.get("provider", providers[0])

    def clean_model_name(model):
        parts = model.split("/")
        short = parts[-1].split(":")[0]
        return short

    filtered_models = [
        (m, clean_model_name(m))
        for m in model_list
        if m.split("/")[1] == selected_provider
    ]

    selected_model = request.GET.get(
        "model", filtered_models[0][0] if filtered_models else model_list[0]
    )

    # --- Add this block to enforce model-provider consistency ---
    valid_model_values = [m for m, _ in filtered_models]
    if selected_model not in valid_model_values:
        if filtered_models:
            first_model = filtered_models[0][0]
            params = request.GET.copy()
            params["model"] = first_model
            return redirect(f"{request.path}?{params.urlencode()}")
        else:
            raise Http404("No models available for this provider.")
    # --- End block ---

    queries = list(results.keys())
    chart_labels = [f"Query {i + 1}" for i in range(len(queries))]
    legend = list(zip(chart_labels, queries))

    # Build the HTML table for the selected model only
    table_html = '<table class="table-auto w-full border border-gray-200 text-center">'
    table_html += '<thead><tr><th class="px-4 py-2 border">Query</th><th class="px-4 py-2 border">{}</th></tr></thead><tbody>'.format(
        clean_model_name(selected_model)
    )
    for label, query in legend:
        table_html += f'<tr><td class="px-4 py-2 border font-semibold">{label}</td>'
        status = results[query]["model_responses"][selected_model].get("status")
        if status == "success":
            icon = '<span class="text-green-600 font-bold text-xl">&#10004;</span>'
        else:
            icon = '<span class="text-red-600 font-bold text-xl">&#10008;</span>'
        table_html += f'<td class="px-4 py-2 border">{icon}</td></tr>'
    table_html += "</tbody></table>"

    nav_links = [
        {"url": reverse("return_status_summary"), "label": "Summary"},
        {"url": reverse("return_status"), "label": "Explore Results"},
    ]

    context = {
        "nav_links": nav_links,
        "success_table_html": mark_safe(table_html),
        "providers": providers,
        "selected_provider": selected_provider,
        "filtered_models": filtered_models,
        "selected_model": selected_model,
        "legend": legend,
        "run_files": run_files,
        "run_choices": run_choices,
        "selected_run": selected_run,
        "section_title": "LLM Return Status",
    }
    return render(request, "comparellm/return_status.html", context)


def query_detail(request, label, model):
    label = unquote(label)
    data_dir = os.path.join(os.path.dirname(__file__), "..", "comparellm", "data")
    run_files = [
        f
        for f in os.listdir(data_dir)
        if f.startswith("llm_comparison_results_") and f.endswith(".json")
    ]

    run_choices = []
    for f in run_files:
        match = re.search(r"_run(\d+)\.json$", f)
        run_number = int(match.group(1)) if match else 0
        run_choices.append((f, run_number))

    # Sort by run_number
    run_choices = sorted(run_choices, key=lambda x: x[1])

    selected_run = request.GET.get("run", run_files[0] if run_files else "")
    results_file = os.path.join(data_dir, selected_run)
    with open(results_file, "r", encoding="utf-8") as f:
        results = json.load(f)
    if isinstance(results, dict) and "run_1" in results:
        results = results["run_1"]

    # Find the query text from the label
    queries = list(results.keys())
    chart_labels = [f"Query {i + 1}" for i in range(len(queries))]
    legend = list(zip(chart_labels, queries))
    query_text = dict(legend).get(label)
    if not query_text:
        raise Http404("Query not found.")

    model_responses = results[query_text]["model_responses"]
    model_data = model_responses.get(model)
    if not model_data:
        raise Http404("Model not found for this query.")

    section = request.GET.get("section", "results")
    if section == "layer_comparison":
        nav_links = [
            {"url": reverse("layer_comparison_summary"), "label": "Summary"},
            {"url": reverse("layer_comparison"), "label": "Explore Results"},
        ]
        section_title = "Layer Comparison vs Ground Truth"
    elif section == "return_status":
        nav_links = [
            {"url": reverse("return_status_summary"), "label": "Summary"},
            {"url": reverse("return_status"), "label": "Explore Results"},
        ]
        section_title = "LLM Return Status"

    context = {
        "nav_links": nav_links,
        "label": label,
        "query": query_text,
        "model": model,
        "model_data": model_data,
        "section_title": section_title,
    }
    return render(request, "comparellm/query_detail.html", context)


def return_status_summary(request):
    data_dir = os.path.join(os.path.dirname(__file__), "..", "comparellm", "data")
    run_files = sorted(
        [
            f
            for f in os.listdir(data_dir)
            if f.startswith("llm_comparison_results_") and f.endswith(".json")
        ]
    )
    run_choices = []
    for f in run_files:
        match = re.search(r"_run(\d+)\.json$", f)
        run_number = int(match.group(1)) if match else 0
        run_choices.append((f, run_number))
    run_choices = sorted(run_choices, key=lambda x: x[1])

    # Get selected run from GET, default to latest
    selected_run = request.GET.get("run", run_choices[-1][0] if run_choices else "")

    total_runs = len(run_files)
    total_queries = 0
    total_models = set()
    pie_data = []
    for run_file in run_files:
        with open(os.path.join(data_dir, run_file), "r", encoding="utf-8") as f:
            results = json.load(f)
        if isinstance(results, dict) and "run_1" in results:
            results = results["run_1"]
        total_queries += len(results)
        for v in results.values():
            total_models.update(v["model_responses"].keys())
        # Extract run number from filename
        match = re.search(r"_run(\d+)\.json$", run_file)
        run_number = int(match.group(1)) if match else 0
        # Count success/error for this run
        success_count = 0
        error_count = 0
        for v in results.values():
            for resp in v["model_responses"].values():
                if resp.get("status") == "success":
                    success_count += 1
                else:
                    error_count += 1
        pie_data.append(
            {
                "run": run_file,
                "run_number": run_number,
                "success": success_count,
                "error": error_count,
            }
        )
    # Sort pie_data by run_number
    pie_data = sorted(pie_data, key=lambda x: x["run_number"])

    # Build all_table_html for selected run
    all_table_html = ""
    if selected_run:
        with open(os.path.join(data_dir, selected_run), "r", encoding="utf-8") as f:
            results = json.load(f)
        if isinstance(results, dict) and "run_1" in results:
            results = results["run_1"]
        queries = list(results.keys())
        chart_labels = [f"Query {i + 1}" for i in range(len(queries))]
        legend = list(zip(chart_labels, queries))
        all_models = set()
        for v in results.values():
            all_models.update(v["model_responses"].keys())
        all_models = sorted(all_models)
        all_table_html = '<table class="table-auto w-full border border-gray-200 text-center text-xs">'
        all_table_html += '<thead><tr><th class="px-2 py-1 border">Query</th>'
        for model in all_models:
            short_name = model.split("/")[-1].split(":")[0]
            all_table_html += f'<th class="px-2 py-1 border">{short_name}</th>'
        all_table_html += "</tr></thead><tbody>"
        for label, query in legend:
            all_table_html += (
                f'<tr><td class="px-2 py-1 border font-semibold">{label}</td>'
            )
            for model in all_models:
                status = results[query]["model_responses"].get(model, {}).get("status")
                if status == "success":
                    icon = (
                        '<span class="text-green-600 font-bold text-lg">&#10004;</span>'
                    )
                elif status == "error":
                    icon = (
                        '<span class="text-red-600 font-bold text-lg">&#10008;</span>'
                    )
                else:
                    icon = '<span class="text-gray-400">—</span>'
                all_table_html += f'<td class="px-2 py-1 border">{icon}</td>'
            all_table_html += "</tr>"
        all_table_html += "</tbody></table>"

    # --- Combined run results table ---
    # Collect all queries and models across all runs
    all_queries = set()
    all_models = set()
    run_results = []

    for run_file in run_files:
        with open(os.path.join(data_dir, run_file), "r", encoding="utf-8") as f:
            results = json.load(f)
        if isinstance(results, dict) and "run_1" in results:
            results = results["run_1"]
        run_results.append(results)
        for query, v in results.items():
            all_queries.add(query)
            all_models.update(v["model_responses"].keys())

    all_queries = sorted(all_queries)
    all_models = sorted(all_models)

    # Build combined table: for each query/model, count successes across runs
    combined_table_html = (
        '<table class="table-auto w-full border border-gray-200 text-center text-xs">'
    )
    combined_table_html += '<thead><tr><th class="px-2 py-1 border">Query</th>'
    for model in all_models:
        short_name = model.split("/")[-1].split(":")[0]
        combined_table_html += f'<th class="px-2 py-1 border">{short_name}</th>'
    combined_table_html += "</tr></thead><tbody>"

    # For each query/model, build a string of check/cross marks for all runs
    for query in all_queries:
        combined_table_html += (
            f'<tr><td class="px-2 py-1 border font-semibold">{query}</td>'
        )
        for model in all_models:
            marks = ""
            for results in run_results:
                if query in results and model in results[query]["model_responses"]:
                    if (
                        results[query]["model_responses"][model].get("status")
                        == "success"
                    ):
                        marks += '<span class="text-green-600 font-bold text-lg">&#10004;</span>'
                    else:
                        marks += '<span class="text-red-600 font-bold text-lg">&#10008;</span>'
                else:
                    marks += '<span class="text-gray-400 font-bold text-lg">&#9675;</span>'  # ◯
            combined_table_html += f'<td class="px-2 py-1 border">{marks}</td>'
        combined_table_html += "</tr>"
    combined_table_html += "</tbody></table>"

    nav_links = [
        {"url": reverse("return_status_summary"), "label": "Summary"},
        {"url": reverse("return_status"), "label": "Explore Results"},
    ]
    context = {
        "nav_links": nav_links,
        "total_runs": total_runs,
        "total_queries": total_queries,
        "total_models": len(total_models),
        "pie_data": pie_data,
        "run_choices": run_choices,
        "selected_run": selected_run,
        "all_table_html": mark_safe(all_table_html),
        "combined_table_html": mark_safe(combined_table_html),
        "section_title": "LLM Return Status",
    }
    return render(request, "comparellm/return_status_summary.html", context)


def layer_comparison(request):
    data_dir = os.path.join(os.path.dirname(__file__), "..", "comparellm", "data")
    with open(os.path.join(data_dir, "ground_truth.json"), "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    run_files = [
        f
        for f in os.listdir(data_dir)
        if f.startswith("llm_comparison_results_") and f.endswith(".json")
    ]
    run_files = sorted(run_files)
    selected_run = request.GET.get("run", run_files[-1] if run_files else "")
    results = {}
    if selected_run:
        with open(os.path.join(data_dir, selected_run), "r", encoding="utf-8") as f:
            results = json.load(f)
        if isinstance(results, dict) and "run_1" in results:
            results = results["run_1"]

    queries = list(results.keys())
    chart_labels = [f"Query {i + 1}" for i in range(len(queries))]
    legend = list(zip(chart_labels, queries))
    all_models = set()
    for v in results.values():
        all_models.update(v["model_responses"].keys())
    all_models = sorted(all_models)

    # Extract providers from model names
    providers = sorted(
        set(m.split("/")[1] for m in all_models if len(m.split("/")) > 1)
    )
    selected_provider = request.GET.get("provider", providers[0] if providers else "")

    # Helper to get short model name
    def clean_model_name(model):
        parts = model.split("/")
        short = parts[-1].split(":")[0]
        return short

    # Filter models by provider and build tuples for the filter
    filtered_models = [
        (m, clean_model_name(m))
        for m in all_models
        if m.split("/")[1] == selected_provider
    ]
    selected_model = request.GET.get(
        "model", filtered_models[0][0] if filtered_models else ""
    )

    # --- Add this block to enforce model-provider consistency ---
    valid_model_values = [m for m, _ in filtered_models]
    if selected_model not in valid_model_values:
        if filtered_models:
            first_model = filtered_models[0][0]
            params = request.GET.copy()
            params["model"] = first_model
            return redirect(f"{request.path}?{params.urlencode()}")
        else:
            raise Http404("No models available for this provider.")
    # --- End block ---

    # Build filtered table: only show selected model (or all if not selected)
    table = []
    for query in queries:
        row = {"query": query, "models": []}
        gt_layers = set(ground_truth.get(query, []))
        for m, _ in filtered_models:
            model_layers = set(
                results[query]["model_responses"].get(m, {}).get("selected_layers", [])
            )
            correct = gt_layers == model_layers
            row["models"].append(
                {
                    "model": m,
                    "model_layers": model_layers,
                    "ground_truth": gt_layers,
                    "is_correct": correct,
                    "missing": gt_layers - model_layers,
                    "extra": model_layers - gt_layers,
                }
            )
        table.append(row)
    nav_links = [
        {"url": reverse("layer_comparison_summary"), "label": "Summary"},
        {"url": reverse("layer_comparison"), "label": "Explore Results"},
    ]

    context = {
        "nav_links": nav_links,
        "run_files": run_files,
        "selected_run": selected_run,
        "providers": providers,
        "selected_provider": selected_provider,
        "filtered_models": filtered_models,  # Now a list of (model, short_name)
        "selected_model": selected_model,
        "table": table,
        "section_title": "Layer Comparison vs Ground Truth",
        "legend": legend,
    }
    return render(request, "comparellm/layer_comparison.html", context)


def layer_comparison_summary(request):
    data_dir = os.path.join(os.path.dirname(__file__), "..", "comparellm", "data")
    run_files = sorted(
        [
            f
            for f in os.listdir(data_dir)
            if f.startswith("llm_comparison_results_") and f.endswith(".json")
        ]
    )
    run_choices = []
    for f in run_files:
        match = re.search(r"_run(\d+)\.json$", f)
        run_number = int(match.group(1)) if match else 0
        run_choices.append((f, run_number))
    run_choices = sorted(run_choices, key=lambda x: x[1])

    selected_run = request.GET.get("run", run_choices[-1][0] if run_choices else "")

    total_runs = len(run_files)
    total_queries = 0
    total_models = set()
    pie_data = []
    for run_file in run_files:
        with open(os.path.join(data_dir, run_file), "r", encoding="utf-8") as f:
            results = json.load(f)
        if isinstance(results, dict) and "run_1" in results:
            results = results["run_1"]
        # Load ground truth
        with open(
            os.path.join(data_dir, "ground_truth.json"), "r", encoding="utf-8"
        ) as gf:
            ground_truth = json.load(gf)
        total_queries += len(results)
        for v in results.values():
            total_models.update(v["model_responses"].keys())
        match = re.search(r"_run(\d+)\.json$", run_file)
        run_number = int(match.group(1)) if match else 0
        correct_count = 0
        incorrect_count = 0
        for query, v in results.items():
            gt_layers = set(ground_truth.get(query, []))
            for model, resp in v["model_responses"].items():
                model_layers = set(resp.get("selected_layers", []))
                if gt_layers == model_layers:
                    correct_count += 1
                else:
                    incorrect_count += 1
        pie_data.append(
            {
                "run": run_file,
                "run_number": run_number,
                "correct": correct_count,
                "incorrect": incorrect_count,
            }
        )
    pie_data = sorted(pie_data, key=lambda x: x["run_number"])

    # Build all_table_html for selected run
    all_table_html = ""
    if selected_run:
        with open(os.path.join(data_dir, selected_run), "r", encoding="utf-8") as f:
            results = json.load(f)
        if isinstance(results, dict) and "run_1" in results:
            results = results["run_1"]
        with open(
            os.path.join(data_dir, "ground_truth.json"), "r", encoding="utf-8"
        ) as gf:
            ground_truth = json.load(gf)
        queries = list(results.keys())
        all_models = set()
        for v in results.values():
            all_models.update(v["model_responses"].keys())
        all_models = sorted(all_models)
        all_table_html = '<table class="table-auto w-full border border-gray-200 text-center text-xs">'
        all_table_html += '<thead><tr><th class="px-2 py-1 border">Query</th>'
        for model in all_models:
            short_name = model.split("/")[-1].split(":")[0]
            all_table_html += f'<th class="px-2 py-1 border">{short_name}</th>'
        all_table_html += "</tr></thead><tbody>"
        for query in queries:
            all_table_html += (
                f'<tr><td class="px-2 py-1 border font-semibold">{query}</td>'
            )
            gt_layers = set(ground_truth.get(query, []))
            for model in all_models:
                model_layers = set(
                    results[query]["model_responses"]
                    .get(model, {})
                    .get("selected_layers", [])
                )
                if gt_layers == model_layers:
                    icon = (
                        '<span class="text-green-600 font-bold text-lg">&#10004;</span>'
                    )
                else:
                    icon = (
                        '<span class="text-red-600 font-bold text-lg">&#10008;</span>'
                    )
                all_table_html += f'<td class="px-2 py-1 border">{icon}</td>'
            all_table_html += "</tr>"
        all_table_html += "</tbody></table>"

    # Collect all queries and models across all runs
    all_queries = set()
    all_models = set()
    run_results = []

    for run_file in run_files:
        with open(os.path.join(data_dir, run_file), "r", encoding="utf-8") as f:
            results = json.load(f)
        if isinstance(results, dict) and "run_1" in results:
            results = results["run_1"]
        run_results.append(results)
        for query, v in results.items():
            all_queries.add(query)
            all_models.update(v["model_responses"].keys())

    all_queries = sorted(all_queries)
    all_models = sorted(all_models)

    # Load ground truth
    with open(os.path.join(data_dir, "ground_truth.json"), "r", encoding="utf-8") as gf:
        ground_truth = json.load(gf)

    # Build combined table: for each query/model, show ✔ or ✘ for each run
    combined_layer_table_html = (
        '<table class="table-auto w-full border border-gray-200 text-center text-xs">'
    )
    combined_layer_table_html += '<thead><tr><th class="px-2 py-1 border">Query</th>'
    for model in all_models:
        short_name = model.split("/")[-1].split(":")[0]
        combined_layer_table_html += f'<th class="px-2 py-1 border">{short_name}</th>'
    combined_layer_table_html += "</tr></thead><tbody>"

    for query in all_queries:
        combined_layer_table_html += (
            f'<tr><td class="px-2 py-1 border font-semibold">{query}</td>'
        )
        for model in all_models:
            marks = ""
            for results in run_results:
                gt_layers = set(ground_truth.get(query, []))
                model_layers = set(
                    results.get(query, {})
                    .get("model_responses", {})
                    .get(model, {})
                    .get("selected_layers", [])
                )
                if model_layers:
                    if gt_layers == model_layers:
                        marks += '<span class="text-green-600 font-bold text-lg">&#10004;</span>'
                    else:
                        marks += '<span class="text-red-600 font-bold text-lg">&#10008;</span>'
                else:
                    marks += '<span class="text-gray-400 font-bold text-lg">&#9675;</span>'  # ◯
            combined_layer_table_html += f'<td class="px-2 py-1 border">{marks}</td>'
        combined_layer_table_html += "</tr>"
    combined_layer_table_html += "</tbody></table>"

    nav_links = [
        {"url": reverse("layer_comparison_summary"), "label": "Summary"},
        {"url": reverse("layer_comparison"), "label": "Explore Results"},
    ]
    context = {
        "nav_links": nav_links,
        "total_runs": total_runs,
        "total_queries": total_queries,
        "total_models": len(total_models),
        "pie_data": pie_data,
        "run_choices": run_choices,
        "selected_run": selected_run,
        "all_table_html": mark_safe(all_table_html),
        "combined_layer_table_html": mark_safe(combined_layer_table_html),
        "section_title": "Selected Layer vs Ground Truth Summary",
    }
    return render(request, "comparellm/layer_comparison_summary.html", context)


def merged_summary(request):
    data_dir = os.path.join(os.path.dirname(__file__), "..", "comparellm", "data")
    run_files = sorted(
        [
            f
            for f in os.listdir(data_dir)
            if f.startswith("llm_comparison_results_") and f.endswith(".json")
        ]
    )

    pie_data = []
    merged_table_html = ""
    all_models = set()
    all_queries = set()

    # Collect all models and queries across all runs
    for run_file in run_files:
        with open(os.path.join(data_dir, run_file), "r", encoding="utf-8") as f:
            results = json.load(f)
        if isinstance(results, dict) and "run_1" in results:
            results = results["run_1"]
        all_queries.update(results.keys())
        for v in results.values():
            all_models.update(v["model_responses"].keys())
    all_models = sorted(all_models)
    all_queries = sorted(all_queries)
    chart_labels = [f"Query {i + 1}" for i in range(len(all_queries))]
    legend = list(zip(chart_labels, all_queries))

    # Pie data for each run
    for run_file in run_files:
        with open(os.path.join(data_dir, run_file), "r", encoding="utf-8") as f:
            results = json.load(f)
        if isinstance(results, dict) and "run_1" in results:
            results = results["run_1"]
        with open(
            os.path.join(data_dir, "ground_truth.json"), "r", encoding="utf-8"
        ) as gf:
            ground_truth = json.load(gf)
        match = re.search(r"_run(\d+)\.json$", run_file)
        run_number = int(match.group(1)) if match else 0

        success_correct = 0
        success_incorrect = 0
        error_incorrect = 0

        for label, query in legend:
            for model in all_models:
                status = (
                    results.get(query, {})
                    .get("model_responses", {})
                    .get(model, {})
                    .get("status")
                )
                gt_layers = set(ground_truth.get(query, []))
                model_layers = set(
                    results.get(query, {})
                    .get("model_responses", {})
                    .get(model, {})
                    .get("selected_layers", [])
                )
                is_correct = gt_layers == model_layers
                if status == "success" and is_correct:
                    success_correct += 1
                elif status == "success" and not is_correct:
                    success_incorrect += 1
                elif status != "success":
                    error_incorrect += 1

        pie_data.append(
            {
                "run_number": run_number,
                "success_correct": success_correct,
                "success_incorrect": success_incorrect,
                "error_incorrect": error_incorrect,
            }
        )

    # Use latest run for merged table
    selected_run = run_files[-1] if run_files else ""
    if selected_run:
        with open(os.path.join(data_dir, selected_run), "r", encoding="utf-8") as f:
            results = json.load(f)
        if isinstance(results, dict) and "run_1" in results:
            results = results["run_1"]
        with open(
            os.path.join(data_dir, "ground_truth.json"), "r", encoding="utf-8"
        ) as gf:
            ground_truth = json.load(gf)
        merged_table_html = '<table class="table-auto w-full border border-gray-200 text-center text-xs">'
        merged_table_html += '<thead><tr><th class="px-2 py-1 border">Query</th>'
        for model in all_models:
            short_name = model.split("/")[-1].split(":")[0]
            merged_table_html += f'<th class="px-2 py-1 border">{short_name}</th>'
        merged_table_html += "</tr></thead><tbody>"
        for label, query in legend:
            merged_table_html += (
                f'<tr><td class="px-2 py-1 border font-semibold">{label}</td>'
            )
            for model in all_models:
                status = (
                    results.get(query, {})
                    .get("model_responses", {})
                    .get(model, {})
                    .get("status")
                )
                gt_layers = set(ground_truth.get(query, []))
                model_layers = set(
                    results.get(query, {})
                    .get("model_responses", {})
                    .get(model, {})
                    .get("selected_layers", [])
                )
                is_correct = gt_layers == model_layers
                if status == "success" and is_correct:
                    cell = '<span class="text-green-600 font-bold text-lg">&#10004;&#10004;</span>'
                elif status == "success" and not is_correct:
                    cell = '<span class="text-yellow-600 font-bold text-lg">&#10004;&#10008;</span>'
                else:
                    cell = '<span class="text-red-600 font-bold text-lg">&#10008;&#10008;</span>'
                merged_table_html += f'<td class="px-2 py-1 border">{cell}</td>'
            merged_table_html += "</tr>"
        merged_table_html += "</tbody></table>"

    nav_links = [
        {"url": reverse("return_status_summary"), "label": "Return Status Summary"},
        {
            "url": reverse("layer_comparison_summary"),
            "label": "Layer Comparison Summary",
        },
    ]
    context = {
        "pie_data": sorted(pie_data, key=lambda x: x["run_number"]),
        "nav_links": nav_links,
        "merged_table_html": mark_safe(merged_table_html),
        "section_title": "Merged Summary: Return Status vs Ground Truth",
    }
    return render(request, "comparellm/merged_summary.html", context)


def model_rankings(request):
    data_dir = os.path.join(os.path.dirname(__file__), "..", "comparellm", "data")
    run_files = sorted(
        [
            f
            for f in os.listdir(data_dir)
            if f.startswith("llm_comparison_results_") and f.endswith(".json")
        ]
    )

    # Collect all models, queries, and runs
    all_models = set()
    all_queries = set()
    run_results = []

    for run_file in run_files:
        with open(os.path.join(data_dir, run_file), "r", encoding="utf-8") as f:
            results = json.load(f)
        if isinstance(results, dict) and "run_1" in results:
            results = results["run_1"]
        run_results.append(results)
        for query, v in results.items():
            all_queries.add(query)
            all_models.update(v["model_responses"].keys())

    all_models = sorted(all_models)
    all_queries = sorted(all_queries)
    total_runs = len(run_files)
    total_possible = len(all_queries) * total_runs

    # Calculate success rate for each model
    model_stats = []
    for model in all_models:
        success_count = 0
        for results in run_results:
            for query in all_queries:
                status = (
                    results.get(query, {})
                    .get("model_responses", {})
                    .get(model, {})
                    .get("status")
                )
                if status == "success":
                    success_count += 1
        rate = (success_count / total_possible) * 100 if total_possible else 0
        model_stats.append(
            {
                "model": model,
                "short_name": model.split("/")[-1].split(":")[0],
                "success_count": success_count,
                "total": total_possible,
                "success_rate": rate,
            }
        )

    # Sort by success rate descending
    model_stats.sort(key=lambda x: x["success_rate"], reverse=True)

    # Build HTML table
    table_html = (
        '<table class="table-auto w-full border border-gray-200 text-center text-sm">'
    )
    table_html += '<thead><tr><th class="px-2 py-1 border">Model</th><th class="px-2 py-1 border">Successes</th><th class="px-2 py-1 border">Total</th><th class="px-2 py-1 border">Success Rate</th></tr></thead><tbody>'
    for stat in model_stats:
        table_html += (
            f'<tr><td class="px-2 py-1 border font-semibold">{stat["short_name"]}</td>'
        )
        table_html += f'<td class="px-2 py-1 border">{stat["success_count"]}</td>'
        table_html += f'<td class="px-2 py-1 border">{stat["total"]}</td>'
        table_html += (
            f'<td class="px-2 py-1 border">{stat["success_rate"]:.1f}%</td></tr>'
        )
    table_html += "</tbody></table>"

    ranking_nav_links = [
        {"url": reverse("model_rankings"), "label": "Overall Success Rate"},
        {"url": reverse("model_correctness_rankings"), "label": "Correctness Rate"},
    ]
    context = {
        "section_title": "Model Rankings (Overall Success Rate)",
        "table_html": mark_safe(table_html),
        "ranking_nav_links": ranking_nav_links,
    }
    return render(request, "comparellm/model_rankings.html", context)


def model_correctness_rankings(request):
    data_dir = os.path.join(os.path.dirname(__file__), "..", "comparellm", "data")
    run_files = sorted(
        [
            f
            for f in os.listdir(data_dir)
            if f.startswith("llm_comparison_results_") and f.endswith(".json")
        ]
    )

    # Collect all models, queries, and runs
    all_models = set()
    all_queries = set()
    run_results = []

    for run_file in run_files:
        with open(os.path.join(data_dir, run_file), "r", encoding="utf-8") as f:
            results = json.load(f)
        if isinstance(results, dict) and "run_1" in results:
            results = results["run_1"]
        run_results.append(results)
        for query, v in results.items():
            all_queries.add(query)
            all_models.update(v["model_responses"].keys())

    all_models = sorted(all_models)
    all_queries = sorted(all_queries)
    total_runs = len(run_files)
    total_possible = len(all_queries) * total_runs

    # Load ground truth
    with open(os.path.join(data_dir, "ground_truth.json"), "r", encoding="utf-8") as gf:
        ground_truth = json.load(gf)

    # Calculate correctness rate for each model
    model_stats = []
    for model in all_models:
        correct_count = 0
        for results in run_results:
            for query in all_queries:
                gt_layers = set(ground_truth.get(query, []))
                model_layers = set(
                    results.get(query, {})
                    .get("model_responses", {})
                    .get(model, {})
                    .get("selected_layers", [])
                )
                if gt_layers == model_layers and model_layers:
                    correct_count += 1
        rate = (correct_count / total_possible) * 100 if total_possible else 0
        model_stats.append(
            {
                "model": model,
                "short_name": model.split("/")[-1].split(":")[0],
                "correct_count": correct_count,
                "total": total_possible,
                "correctness_rate": rate,
            }
        )

    # Sort by correctness rate descending
    model_stats.sort(key=lambda x: x["correctness_rate"], reverse=True)

    # Build HTML table
    table_html = (
        '<table class="table-auto w-full border border-gray-200 text-center text-sm">'
    )
    table_html += '<thead><tr><th class="px-2 py-1 border">Model</th><th class="px-2 py-1 border">Correct Matches</th><th class="px-2 py-1 border">Total</th><th class="px-2 py-1 border">Correctness Rate</th></tr></thead><tbody>'
    for stat in model_stats:
        table_html += (
            f'<tr><td class="px-2 py-1 border font-semibold">{stat["short_name"]}</td>'
        )
        table_html += f'<td class="px-2 py-1 border">{stat["correct_count"]}</td>'
        table_html += f'<td class="px-2 py-1 border">{stat["total"]}</td>'
        table_html += (
            f'<td class="px-2 py-1 border">{stat["correctness_rate"]:.1f}%</td></tr>'
        )
    table_html += "</tbody></table>"

    ranking_nav_links = [
        {"url": reverse("model_rankings"), "label": "Overall Success Rate"},
        {"url": reverse("model_correctness_rankings"), "label": "Correctness Rate"},
    ]

    context = {
        "section_title": "Model Rankings (Correctness Rate)",
        "table_html": mark_safe(table_html),
        "ranking_nav_links": ranking_nav_links,
    }
    return render(request, "comparellm/model_rankings.html", context)


def home(request):
    return render(request, "comparellm/home.html")
