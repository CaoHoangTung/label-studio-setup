const WINDOW_SIZE = 50;
function debounce(func, timeout = 300) {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => {
            func.apply(this, args);
        }, timeout);
    };
}
const AXES = ["x", "y", "z"]
const AXES_COLORS = {x: "blue", y: "red", z: "green"};
document.addEventListener("DOMContentLoaded", async (event) => {
    window.setTotalVideoTime = function () {
        const videoElement = document.querySelector("video");
        const videoEndElement = document.getElementById("video-end");
        const v = parseInt(videoEndElement.value);
        if (!isNaN(v) && v > 0) {
            return;
        }
        videoEndElement.value = videoElement.duration * videoElement.playbackRate;
    };

    const sensorData = await fetch(
        "{{ url_for('get_dataset_processed_file', dataset_id=dataset_id, filename='sensor.json') }}",
    ).then((response) => {
        if (!response.ok) {
            throw new Error("HTTP error " + response.status);
        }
        return response.json();
    });
    document.getElementById("sensor-data-loader").classList.add("hidden")
    document.getElementById("sensor-data-sections").classList.replace("hidden", "flex")

    const s1Slider = document.getElementById("sensor1-time-slider");
    const s1Input = document.getElementById("sensor1-time-input");
    const s1Start = document.getElementById("sensor1-start");
    const s1End = document.getElementById("sensor1-end");

    s1Slider.max = sensorData.sensor1.size;
    s1Input.max = sensorData.sensor1.size;
    s1End.value = sensorData.sensor1.size;
    s1Start.max = sensorData.sensor1.size;
    s1End.max = sensorData.sensor1.size;

    const s2Slider = document.getElementById("sensor2-time-slider");
    const s2Input = document.getElementById("sensor2-time-input");
    const s2Start = document.getElementById("sensor2-start");
    const s2End = document.getElementById("sensor2-end");
    s2Slider.max = sensorData.sensor2.size;
    s2Input.max = sensorData.sensor2.size;
    s2End.value = sensorData.sensor2.size;
    s2Start.max = sensorData.sensor2.size;
    s2End.max = sensorData.sensor2.size;

    let sensor1 = setupChart("sensor1-canvas", sensorData["sensor1"], "sensor1");
    let sensor2 = setupChart("sensor2-canvas", sensorData["sensor2"], "sensor2");
    const sensorChartData = {
        sensor1: sensor1,
        sensor2: sensor2,
    };
    const sensorPosition = {
        sensor1: 0,
        sensor2: 0,
    };

    const sensorActions = {
        sensor1: {},
        sensor2: {},
    };

    window.setVideoPosition = function (positionType) {
        const start = parseInt(document.getElementById("video-start").value);
        const end = parseInt(document.getElementById("video-end").value);
        const videoElement = document.querySelector("video");
        const currentFrame = videoElement.currentTime * videoElement.playbackRate;

        if (positionType === "video-start" && end <= currentFrame) {
            alert("Start time must be less than end time");
            return;
        }

        if (positionType === "video-end" && currentFrame <= start) {
            alert("End time must be more than start time");
            return;
        }

        document.getElementById(positionType).value = currentFrame;
    };

    function label(tooltipItem, sensorName) {
        const actualDataIndex = parseInt(tooltipItem.label);
        let footerContent = "";
        footerContent += tooltipItem.formattedValue + " | ";
        footerContent += sensorData[sensorName].time[actualDataIndex];
        footerContent += "";

        return footerContent;
    }

    function createChartOption(sensorName, scale) {
        return {
            scales: {
                y: {
                    suggestedMax: scale,
                    suggestedMin: -scale,
                },
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: (tooltipItem) => label(tooltipItem, sensorName),
                    },
                },
            },
            animation: false,
        };
    }

    function setupChart(chartId, data, sensorName) {
        // Get the canvas and context

        const chart = {};

        AXES.forEach(axis => {
            const canvas = document.getElementById(chartId + "-" + axis);
            const ctx = canvas.getContext("2d");

            chart[axis] = new Chart(ctx, {
                type: "line",
                data: {
                    labels: Array.from({length: WINDOW_SIZE}, (_, i) => i),
                    datasets: [
                        {
                            label: chartId,
                            data: data[axis].slice(0, WINDOW_SIZE),
                            borderColor: AXES_COLORS[axis],
                            backgroundColor: "transparent",
                        },
                    ],
                },
                options: createChartOption(sensorName, 3),
            });
        })
        // Set up the chart

        return {
            chart: chart,
            originalData: data,
        };
    }

    window.updateChartScale = function (sensorName, newScale) {
        // New scale configuration
        const newScaleOptions = createChartOption(sensorName, newScale);

        AXES.forEach(axis => {
            // Update the chart's options with the new scale options
            const chart = sensorChartData[sensorName].chart[axis];
            chart.config.options = newScaleOptions;
            chart.update();
        })
    };

    // Function to update the chart with current time
    function seekChart(sensorChart, time) {
        const chart = sensorChart.chart;
        const origData = sensorChart.originalData;

        time = parseInt(time);

        AXES.forEach(axis => {
            const a = chart[axis]
            a.options.plugins.tooltip.enabled = false;
            a.options.plugins.tooltip.enabled = true;
            a.data.labels = Array.from({length: WINDOW_SIZE}, (_, i) => i + time);
            a.data.datasets[0].data = origData[axis].slice(time, time + WINDOW_SIZE);
            a.update();
        });
    }

    // Function to seek to a specific time in the animation
    window.seekSensorTime = function (time, sensorName, inputElementType) {
        seekChart(sensorChartData[sensorName], time);

        sensorPosition[sensorName] = time;

        if (inputElementType === "slider") {
            document.getElementById(`${sensorName}-time-input`).value = time;
        } else {
            document.getElementById(`${sensorName}-time-slider`).value = time;
        }
    };

    window.seekSensorTimeDebounced = debounce(window.seekSensorTime, 300)

    window.startSeekStepInterval = function (step, sensorName) {
        seekStep(step, sensorName);
        sensorActions[sensorName].interval = setInterval(() => {
            seekStep(step, sensorName);
        }, 100);
    };

    window.stopSeekStepInterval = function (sensorName) {
        clearInterval(sensorActions[sensorName].interval);
    };

    function seekStep(step, sensorName) {
        let newTime = sensorPosition[sensorName] + step;
        newTime = Math.max(0, newTime);
        newTime = Math.min(newTime, sensorData[sensorName].x.length);
        document.getElementById(`${sensorName}-time-slider`).value = newTime;
        document.getElementById(`${sensorName}-time-input`).value = newTime;
        seekSensorTime(newTime, sensorName);
    }

    window.setSensorPosition = function (sensorName, positionType) {
        document.getElementById(positionType).value = sensorPosition[sensorName];
    };
});
