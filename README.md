# FreqShow

FreqShow is a compact SDR spectrum and waterfall display built to feel like a purpose-built embedded radio tool rather than a desktop application. It is designed around a small touchscreen form factor and runs on a Raspberry Pi Zero 2 W with an RTL-SDR, providing live RF visualization and touch-friendly tuning controls.

This project is based on the original Freq Show work from Adafruit and extends that foundation into a more embedded, touchscreen-focused implementation for compact dedicated hardware.

---

## Credit

Original Freq Show concept and application work credit goes to **Adafruit**.

This repository builds on that original work and adapts it for a different hardware layout, embedded-style presentation, and updated interaction model.

Please see the original Adafruit project for the upstream inspiration and foundation that made this version possible.

---

## Overview

FreqShow is intended to provide a clean, responsive way to view RF activity and interact with an SDR on a small LCD display. The interface is optimized for touchscreen use and focuses on the most important functions without clutter.

The application now behaves much more like an embedded appliance, with controls layered over the live RF display and direct touch interaction for tuning.

---

## Hardware

This build is currently designed around the following hardware:

- **Raspberry Pi Zero 2 W**
- **Waveshare 3.5" LCD (F) with pogo pins**
- **NooElec NESDR Smart**
- Touchscreen input via the Waveshare display
- Portable power-friendly form factor suitable for embedded or field use

### Hardware Notes

#### Raspberry Pi Zero 2 W
The Raspberry Pi Zero 2 W serves as the main compute platform for the application. Its size, low power consumption, and wireless connectivity make it a good fit for a dedicated SDR display.

#### Waveshare 3.5" LCD (F)
The Waveshare 3.5" LCD (F) provides the main user interface and touch input. The pogo-pin design keeps the hardware stack compact and clean, which helps the project feel more like an integrated device and less like a bench prototype.

#### NooElec NESDR Smart
The NooElec NESDR Smart acts as the RF frontend for receiving and displaying spectrum and waterfall data. It provides a simple and reliable USB SDR option for a portable visualization build.

---

## Features

### Live Spectrum Display
FreqShow displays a real-time spectrum view of the selected frequency range, allowing you to quickly identify nearby signals and monitor RF activity.

### Live Waterfall
A continuously updating waterfall provides a visual history of activity over time, making it easier to spot intermittent or drifting signals.

### Touch-Friendly On-Screen Controls
The interface includes simple on-screen controls designed for a small touchscreen environment.

Current controls include:

- **Tune**
- **Switch**
- **Find**

These controls are displayed directly over the live RF visualization so the UI feels integrated and efficient.

---

## Functions Added in This Version

This version includes several usability and presentation improvements beyond the original base implementation.

### Center Frequency Save / Load
The application now saves and restores the center frequency so the device comes back up where you last left it. This makes the experience feel more polished and practical for repeat use.

### Waterfall Behind the Buttons
The live waterfall now continues behind the control buttons instead of leaving a flat black area in the background. This gives the UI a more cohesive and professional look, making the controls feel like they are floating on top of the RF display.

### Tap-to-Tune on Spectrum / Waterfall
You can now tap directly on the spectrum or waterfall to retune to that point. This makes interaction much more natural and dramatically improves usability on a touchscreen device.

### Smooth Retune Behavior
Retuning no longer requires the waterfall to fully clear each time. Instead, the display can slide and continue more naturally, preserving visual continuity and making tuning feel faster and more refined.

### Semi-Transparent Buttons
The Tune, Switch, and Find buttons were updated to be slightly transparent so they sit more cleanly over the live display.

### Cleaner Button Styling
The accent color previously visible on the upper portion of the buttons was removed for a cleaner, more understated embedded-device look.

---

## Embedded UX Goals

A major goal of this version of FreqShow is to feel like a single-purpose device rather than a general-purpose Linux application. The design direction emphasizes:

- Minimal UI clutter
- Fast access to tuning controls
- Live RF information always visible
- Touch-first interaction
- Clear visual hierarchy on a small display
- A polished appliance-like feel

This is why recent changes focused heavily on preserving the waterfall behind controls, reducing visual distractions, and improving direct interaction with the display.

---

## Current Functionality

FreqShow currently supports:

- Real-time SDR spectrum display
- Real-time waterfall rendering
- Touchscreen-friendly control buttons
- Direct tap-to-tune interaction
- Persistent center frequency across sessions
- Improved retuning behavior with smoother visual continuity
- Lightweight embedded-style interface suitable for compact hardware

---

## Platform Summary

**Target Platform**
- Raspberry Pi Zero 2 W

**Display**
- Waveshare 3.5" LCD (F) with pogo pins

**SDR**
- NooElec NESDR Smart

**Primary Use Case**
- Portable embedded spectrum and waterfall viewer with touch tuning

---

## Development Direction

The long-term direction of the project is to continue refining FreqShow into a polished embedded SDR viewer with an emphasis on simplicity, responsiveness, and field usability.

Possible future refinements may include:

- startup polish
- splash or boot screen
- additional tuning tools
- improved search / find behavior
- more settings persistence
- further UI cleanup and embedded-device styling

---

## Why This Version Exists

Many SDR applications are powerful but feel desktop-oriented, even when squeezed onto smaller displays. This version of FreqShow takes a different approach by focusing on a dedicated, constrained interface that works well on a very small touchscreen and feels appropriate for embedded deployment.

The goal is not just to show RF data, but to do it in a way that feels intentional, tactile, and efficient while still acknowledging and building from the original Adafruit work.

---

## Status

FreqShow is currently in active development and has already reached a point where it feels much closer to a purpose-built embedded application than a simple prototype.

Recent interface and behavior improvements have significantly improved the overall experience, especially on the Raspberry Pi Zero 2 W and Waveshare touchscreen hardware combination.

---

## Development Philosophy

When adding features, the priority is to preserve the following:

1. Simple interaction
2. Fast visual feedback
3. Small-screen usability
4. Embedded-device feel
5. Minimal UI complexity

Every new change should support the idea that FreqShow is a dedicated RF tool, not just a generic SDR application running on a Pi.
