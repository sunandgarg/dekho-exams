from multiprocessing import get_context

def revise_receipt(quantity, outbound):
    outbound.put(quantity + 1)

if __name__ == "__main__":
    context = get_context("spawn")
    outbound = context.Queue()
    worker = context.Process(target=revise_receipt, args=(46, outbound))
    worker.start()
    print("revision", outbound.get(timeout=3))
    worker.join(timeout=3)
    print("exit", worker.exitcode)
    outbound.close()
    outbound.join_thread()
