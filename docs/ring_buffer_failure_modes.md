# Ring Buffer Failure Modes

## Overview

The ring buffer uses a fixed-size memory-mapped file to transfer binary order records between processes. This document describes the failure cases tested so far and the current limitations.

## 1. Corrupted Binary Records

The `put()` method validates an order before writing it, but `get()` does not perform full validation after reading the stored record.

The following cases have been tested:

| Corrupted field | Current behaviour |
|---|---|
| Invalid `side` (255) | `get()` raises `ValueError` |
| Invalid `order_type` (255) | `get()` raises `ValueError` |
| `quantity = 0` | `get()` returns an order with zero quantity; calling `validate()` raises `ValueError` |
| `price_ticks = 0` | `get()` returns an order with zero price; calling `validate()` raises `ValueError` |

Currently, `get()` advances the read position before constructing and validating the returned order. If enum conversion fails, the corrupted record has already been consumed.

There is no automatic recovery or quarantine mechanism for corrupted records.

## 2. Full Buffer

When the buffer reaches its capacity, `put()` returns `False` without overwriting unread records.

The producer must retry, wait, or handle the rejected write. The ring buffer does not provide automatic backpressure.

## 3. Process Synchronization

Multiple processes must use the same multiprocessing-compatible lock when accessing the shared buffer.

The default `threading.Lock` only synchronizes threads within one process and does not protect access across independent processes.

## 4. Process Crashes

Automatic crash recovery is not implemented.

An unexpected process termination can leave an operation incomplete or the buffer in an inconsistent state. There is no built-in recovery procedure to verify or repair corrupted shared state.

## 5. Shared File and Configuration

Processes must use the same backing file, capacity, and binary record format.

The implementation checks the file size and stored capacity when opening an existing buffer, but it does not provide comprehensive corruption detection or integrity checks.

## 6. Current Testing Scope

The tests cover basic FIFO behaviour, full-buffer handling, wrap-around, cross-process communication, and selected corrupted fields.

The 1M-order integration test verifies sequential delivery across two processes, full-buffer retries, and repeated wrap-around. The wrap-around count is calculated from the successful order count and buffer capacity rather than measured by an internal counter.

These tests do not establish crash recovery, fault tolerance, or production reliability.

## Future Improvements

Possible improvements include validating orders after reading, handling corrupted records explicitly, and introducing recovery mechanisms for unexpected process failures. Any implementation changes should be reviewed before modifying the current ring buffer behaviour or binary format.