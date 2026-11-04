# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Delegated: the user granted full freedom (2026-11-04). Chosen: FastAPI with server-rendered Jinja templates, plus hand-written CSS and vanilla JavaScript served by the app itself. No build step and no browser-side CDN, so the Docker image stays the whole deliverable and the pages load from the LAN service alone.

## Users

Two audiences with equal weight:

- People in a household with an HDHomeRun tuner who open the TV guide to find what is on. They use a phone, a tablet, a laptop or desktop, and the TV's own browser from the couch, driven by a remote.
- Self-hosters who run the service for Jellyfin, Plex or Emby and open the dashboard to check the cache and the configuration.

## Product Purpose

Turn the guide data of an HDHomeRun tuner into standard XMLTV for media servers, and offer a guide in the browser that is comfortable and simple to explore. Success means two things: the XMLTV is as complete as the source allows, and anyone in the house finds what is on in a few seconds.

## Positioning

A small service that runs next to the tuner on the LAN, uses the device's own guide data with no third-party listings subscription, caches it locally, and ships its own TV guide alongside the XMLTV feed.

## Operating Context

- Media servers (Jellyfin, Plex, Emby) fetch `/epg.xml` on their own schedule.
- Source data: the tuner on the LAN (`discover.json`, `lineup.json`) and SiliconDust's cloud guide (`api.hdhomerun.com/api/guide.php`, authenticated by the rotating `DeviceAuth`).
- Guide horizon, verified on the reference device on 2026-11-04: `guide.php` answers HTTP 400 for any `Start` more than 48 hours ahead, and each call returns about 7 hours of programmes. SiliconDust documents 3 days of guide data for free and 14 days with a DVR subscription.
- SiliconDust also publishes an official XMLTV feed (`api.hdhomerun.com/api/xmltv`). On the reference device, matched programme by programme, it is markedly richer than `guide.php`: descriptions on 95% of programmes instead of 54%, categories on every programme instead of 55%, plus `dd_progid`, video quality and live flags that `guide.php` lacks. It repeats one channel id across several channel numbers, so it is not valid XMLTV as served.
- Reference device: HDHomeRun CONNECT QUATRO (HDHR5-4DT, DVB-T, Italy). It has 317 channels in the lineup, 162 of them with guide data, and logos for 134 of those. Content is mostly Italian.
- Deployment: Docker image on GHCR, plus Helm, ArgoCD and Flux manifests in `deploy/`.

## Capabilities and Constraints

- Endpoints: `/` (dashboard in HTML, status in JSON), `/guide`, `/epg.xml`, `/healthcheck`, `GET` and `DELETE /cache`, `/docs`.
- Configuration through `HDHOMERUN_*` environment variables.
- Guide data per programme: title, episode title and number, synopsis, start and end, original air date, image, poster, series ID, "first airing" flag, genre filter, and teams for sports. Per channel: number, name, affiliate, logo.
- Open decision: whether `/epg.xml` should be built from the official XMLTV feed, from `guide.php`, or from both merged.

## Brand Commitments

- Name: "HDHomeRun EPG" (repository HDHomeRunEPG-to-XmlTv).
- It is a fork and modernization of IncubusVictim's HDHomeRunEPG-to-XmlTv, and the README credits that project.
- HDHomeRun is SiliconDust's product name. This project is not affiliated with SiliconDust.
- No logo or other brand assets exist.

## Evidence on Hand

- A live tuner on the LAN provides real guide data for design and testing.
- `images/` holds screenshots of the previous interface.
- There are no testimonials, user counts or benchmarks; never invent them.

## Product Principles

1. The XMLTV is the product: it carries everything the source provides, and the guide never shows less than the feed knows.
2. Finding what is on comes first: the guide is the front door, and the dashboard is maintenance.
3. Every screen in the house works, from a phone in hand to a TV browser driven by a remote.
4. State is honest: stale, missing and failed data are shown plainly, never as an empty success.

## Accessibility & Inclusion

The guide must be fully operable with arrow keys and Enter, because a TV remote drives the TV browser, and readable from couch distance on a TV. Text and controls meet WCAG 2.2 AA contrast.
