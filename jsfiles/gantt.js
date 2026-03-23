import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

export async function renderTaskGantt(jsonFile, containerSelector = "#schedule-container") {
    const rawTasks = await d3.json(jsonFile);

    const tasks = rawTasks
        .map((task) => ({
            ...task,
            startDate: task.earlystart ? new Date(task.earlystart) : null,
            finishDate: task.earlyfinish ? new Date(task.earlyfinish) : null
        }))
        .filter((task) => task.startDate && task.finishDate)
        .sort((a, b) => a.startDate - b.startDate || a.id - b.id);

    const container = d3.select(containerSelector);
    container.selectAll("*").remove();

    if (!tasks.length) {
        container
            .append("p")
            .text("No scheduled tasks found in the JSON file.");
        return;
    }

    const margin = { top: 30, right: 30, bottom: 50, left: 220 };
    const width = 1100;
    const rowHeight = 28;
    const height = margin.top + margin.bottom + tasks.length * rowHeight;

    const minStart = d3.min(tasks, (task) => task.startDate);
    const maxFinish = d3.max(tasks, (task) => task.finishDate);

    const xScale = d3
        .scaleTime()
        .domain([d3.timeDay.offset(minStart, -1), d3.timeDay.offset(maxFinish, 1)])
        .range([margin.left, width - margin.right]);

    const yScale = d3
        .scaleBand()
        .domain(tasks.map((task) => `${task.id}: ${task.name}`))
        .range([margin.top, height - margin.bottom])
        .padding(0.2);

    const svg = container
        .append("svg")
        .attr("width", width)
        .attr("height", height)
        .attr("viewBox", [0, 0, width, height]);

    const xAxis = d3.axisBottom(xScale).ticks(d3.timeDay.every(1)).tickFormat(d3.timeFormat("%Y-%m-%d"));
    const yAxis = d3.axisLeft(yScale);

    svg
        .append("g")
        .attr("transform", `translate(0,${height - margin.bottom})`)
        .call(xAxis)
        .call((group) => group.selectAll("text").attr("transform", "rotate(-35)").style("text-anchor", "end"));

    svg
        .append("g")
        .attr("transform", `translate(${margin.left},0)`)
        .call(yAxis);

    svg
        .append("g")
        .selectAll("rect")
        .data(tasks)
        .join("rect")
        .attr("x", (task) => xScale(task.startDate))
        .attr("y", (task) => yScale(`${task.id}: ${task.name}`))
        .attr("width", (task) => Math.max(2, xScale(task.finishDate) - xScale(task.startDate)))
        .attr("height", yScale.bandwidth())
        .attr("fill", "steelblue");

    svg
        .append("g")
        .selectAll("text")
        .data(tasks)
        .join("text")
        .attr("x", (task) => xScale(task.startDate) + 6)
        .attr("y", (task) => yScale(`${task.id}: ${task.name}`) + yScale.bandwidth() / 2 + 4)
        .attr("fill", "white")
        .style("font-size", "11px")
        .text((task) => `${task.duration}d`);
}