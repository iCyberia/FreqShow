# FreqShow

FreqShow is a compact SDR spectrum and waterfall display for small touchscreen hardware. This version is designed to run on a **Raspberry Pi Zero 2 W** with a **Waveshare 3.5" LCD (F)** and a **NooElec NESDR Smart**, giving it the feel of a dedicated embedded RF tool rather than a desktop SDR application.

> Based on the original **Freq Show** project by **Adafruit**. Credit for the original concept and application belongs to Adafruit.

## Hardware

This build is currently designed around:

- **Raspberry Pi Zero 2 W**
- **Waveshare 3.5" LCD (F)** with pogo pins
- **NooElec NESDR Smart**
- Touch input via the Waveshare display

## What This Version Adds

This version extends the original application with a more embedded, touchscreen-focused interface and several usability improvements:

- **Center frequency save/load** so the app restores the last tuned frequency on startup
- **Waterfall behind the buttons** so the controls appear to float over the live display
- **Tap-to-tune** by touching the spectrum or waterfall
- **Smooth retune behavior** so the waterfall shifts more naturally instead of fully clearing
- **Semi-transparent buttons** for a cleaner overlay effect
- **Cleaner button styling** with the previous top accent removed

## Features

- Real-time SDR spectrum display
- Real-time waterfall display
- Touch-friendly on-screen controls
- Embedded-style interface optimized for a small LCD
- Persistent center frequency between sessions

## Goals

The goal of this version of FreqShow is to provide a clean, responsive RF display that works well on compact touchscreen hardware and feels like a purpose-built device.

Future refinements may include:

- splash screen / boot polish
- additional tuning tools
- improved find/search behavior
- more settings persistence
- continued UI cleanup

## Status

FreqShow is in active development and has already evolved into a much more appliance-like embedded application, especially on the Raspberry Pi Zero 2 W and Waveshare touchscreen combination.
