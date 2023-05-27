import multiprocessing
import time
import logging
import script1, script2, script3, script4, script5

def run_script(script_main):
    try:
        script_main()
        return "Success"
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    # Configure logging to save logs to a file
    logging.basicConfig(filename="script_logs.txt", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    num_cores = multiprocessing.cpu_count()  # Get the number of CPU cores
    processes = []
    results = {}

    # Adjust the number of processes based on the available CPU cores (M1 Max has 8 cores)
    num_processes = min(8, 5)  # Limit to 5 processes or maximum available cores

    # Start the processes
    for i in range(num_processes):
        if i == 0:
            target_script = script1.main
        elif i == 1:
            target_script = script2.main
        elif i == 2:
            target_script = script3.main
        elif i == 3:
            target_script = script4.main
        elif i == 4:
            target_script = script5.main
        processes.append(multiprocessing.Process(target=run_script, args=(target_script,)))

    # Start the processes and record their start time
    start_time = time.time()
    for process in processes:
        process.start()
        results[process] = {"status": "Running", "start_time": start_time}

    # Check the status of each process
    while any(process.is_alive() for process in processes):
        for process in processes:
            if process.is_alive():
                # Check if the process has been running for more than 30 seconds
                elapsed_time = time.time() - results[process]["start_time"]
                if elapsed_time > 30:
                    results[process]["status"] = "Running (Delayed)"
            else:
                # Process has completed
                results[process]["status"] = "Completed"

    # Save the results to the log file
    with open("script_logs.txt", "a") as file:
        for process, result in results.items():
            log_message = f"Process: {process.name}, Status: {result['status']}"
            logging.info(log_message)
            file.write(log_message + "\n")

    # Print the results
    for process, result in results.items():
        print(f"Process: {process.name}, Status: {result['status']}")
