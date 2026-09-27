# AI Interaction Log — System Detective

Assistant used: ChatGPT

This log records AI-assisted work on the CIE-1 activity. Machine-dependent values were checked against the captured Linux/WSL evidence rather than guessed.

## Entry 1 — AI guidance on memory

**Prompt**
Explain how to interpret `free -h`, especially the difference between `free`, `buff/cache`, and `available`.

**AI guidance**
`free` is currently unused memory. `buff/cache` is memory used by the kernel for buffers and cache and can often be reclaimed. `available` is the kernel's estimate of memory that can be given to new allocations without swapping, so it is generally a better indicator of immediately usable memory than `free` alone.

**Machine check**
The captured WSL output was:

```text
Mem:           6.1Gi       313Mi       5.0Gi        72Ki       1.1Gi       5.8Gi
Swap:          2.0Gi          0B       2.0Gi
```

**Conclusion**
The observed numbers must be taken from the command output. In particular, `available` is 5.8 GiB, not a value obtained by subtracting only `free` from `total`.

## Entry 2 — AI guidance on locality

**Prompt**
Why should row-major traversal of a C 2D array be faster than column-major traversal?

**AI guidance**
C stores a two-dimensional array in row-major order. Traversing across a row accesses nearby addresses, which uses spatial locality and cache lines efficiently. Traversing down a column jumps by an entire row between accesses, reducing locality and increasing cache and translation overhead.

**Machine check**
The saved experiment contains three runs, with means of 0.094517 s for row-major traversal and 0.526548 s for column-major traversal, a measured ratio of 5.57×.

**Conclusion**
The direction of the effect was predicted correctly, but the exact timing is empirical. The measured ratio must be reported rather than replaced with a textbook or AI estimate.

## Entry 3 — AI guidance on process states

**Prompt**
What does the `STAT` field in `ps` represent?

**AI guidance**
The state field reports the scheduling state. Common examples include `R` for running/runnable and `S` for interruptible sleep; additional modifiers can provide more detail.

**Machine check**
The captured `ps -eLf` output shows the process/thread table, including PID, LWP and NLWP fields.

**Conclusion**
The dashboard exposes these fields from live `ps` output so the displayed process information can change between refreshes.

## Entry 4 — Real limitation identified

A major risk in AI-assisted system inspection is assuming a generic machine configuration. Earlier draft text used a typical-machine interpretation in places where the WSL environment was not yet verified. The actual `lscpu` output shows an Intel Core i3-4010U environment with 4 logical CPUs, 2 cores, 2 threads/core and Microsoft virtualization.

**Correction**
The final report and dashboard use the verified `lscpu` values and explicitly state that these are measurements from the WSL environment, not generic laptop specifications.
