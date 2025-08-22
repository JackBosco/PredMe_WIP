#include "orderbook_core.hpp"

OrderBookCore::OrderBookCore(double tick_size,
                             const std::vector<LOBEntry>& bids,
                             const std::vector<LOBEntry>& offers)
    : tick_size_(tick_size) {
    const int n = static_cast<int>(1.0 / tick_size_) + 1;
    bids_.assign(n, 0.0);
    offers_.assign(n, 0.0);
    for (const auto& b : bids) {
        int i = price_to_index(b.price);
        if (i >= 0 && i < n) bids_[i] = b.quantity;
    }
    for (const auto& o : offers) {
        int i = price_to_index(o.price);
        if (i >= 0 && i < n) offers_[i] = o.quantity;
    }
}

void OrderBookCore::rebuild_from_tick_change(double new_tick) {
    if (new_tick == tick_size_) return;
    const int newN = static_cast<int>(1.0 / new_tick) + 1;
    const double conv = tick_size_ / new_tick;

    std::vector<double> new_bids(newN, 0.0), new_offers(newN, 0.0);
    for (int i = 0; i < static_cast<int>(bids_.size()); ++i) {
        double qty = bids_[i];
        if (qty != 0.0) {
            int j = static_cast<int>(std::floor(i * conv)); // match Python floor for bids
            if (j >= 0 && j < newN) new_bids[j] += qty;
        }
    }
    for (int i = 0; i < static_cast<int>(offers_.size()); ++i) {
        double qty = offers_[i];
        if (qty != 0.0) {
            int j = static_cast<int>(std::ceil(i * conv)); // match Python ceil for offers
            if (j >= 0 && j < newN) new_offers[j] += qty;
        }
    }
    bids_.swap(new_bids);
    offers_.swap(new_offers);
    tick_size_ = new_tick;
}

void OrderBookCore::set_tick_size(double tick_size) {
    rebuild_from_tick_change(tick_size);
}

bool OrderBookCore::best_bid(double& price_out, double& qty_out) const {
    for (int i = static_cast<int>(bids_.size()) - 1; i >= 0; --i) {
        if (bids_[i] != 0.0) {
            price_out = index_to_price(i);
            qty_out = bids_[i];
            return true;
        }
    }
    return false;
}

bool OrderBookCore::best_offer(double& price_out, double& qty_out) const {
    for (int i = 0; i < static_cast<int>(offers_.size()); ++i) {
        if (offers_[i] != 0.0) {
            price_out = index_to_price(i);
            qty_out = offers_[i];
            return true;
        }
    }
    return false;
}

void OrderBookCore::update_level(const LOBEntry& entry, char side, bool is_delta) {
    int i = price_to_index(entry.price);
    if (i < 0 || i >= static_cast<int>(bids_.size())) return;
    if (side == 'b') {
        if (is_delta) bids_[i] += entry.quantity;
        else bids_[i] = entry.quantity;
    } else {
        if (is_delta) offers_[i] += entry.quantity;
        else offers_[i] = entry.quantity;
    }
}

void OrderBookCore::update_levels(const std::vector<LOBEntry>& entries, char side, bool is_delta) {
    for (const auto& e : entries) update_level(e, side, is_delta);
}

std::vector<Trade> OrderBookCore::add_limit_order(const LOBEntry& entry, char side) {
    std::vector<Trade> trades;
    double order_q = entry.quantity;
    int p = price_to_index(entry.price);
    if (p < 0) p = 0;
    if (p >= static_cast<int>(bids_.size())) p = static_cast<int>(bids_.size()) - 1;
    bool fully_executed = false;

    if (side == 'b') {
        int i = 0;
        while (i < static_cast<int>(offers_.size()) && i <= p) {
            double vol = std::min(order_q, offers_[i]);
            if (vol > 0.0) {
                trades.emplace_back(index_to_price(i), vol);
                offers_[i] -= vol;
                order_q -= vol;
            } else if (order_q == 0.0) {
                fully_executed = true;
                break;
            }
            ++i;
        }
        if (!fully_executed && order_q > 0.0) bids_[p] += order_q;
    } else {
        int i = static_cast<int>(bids_.size()) - 1;
        while (i >= 0 && i >= p) {
            double vol = std::min(order_q, bids_[i]);
            if (vol > 0.0) {
                trades.emplace_back(index_to_price(i), vol);
                bids_[i] -= vol;
                order_q -= vol;
            } else if (order_q == 0.0) {
                fully_executed = true;
                break;
            }
            --i;
        }
        if (!fully_executed && order_q > 0.0) offers_[p] += order_q;
    }

    return trades;
}

double OrderBookCore::tick_size() const { return tick_size_; }

std::pair<std::vector<std::pair<double,double>>, double> OrderBookCore::get_col() const {
    std::vector<std::pair<double,double>> ladder;

    // lowest offer index
    int o = -1;
    for (int i = 0; i < static_cast<int>(offers_.size()); ++i) {
        if (offers_[i] != 0.0) { o = i; break; }
    }

    // highest bid index
    int b = -1;
    for (int i = static_cast<int>(bids_.size()) - 1; i >= 0; --i) {
        if (bids_[i] != 0.0) { b = i; break; }
    }

    // Fallbacks to avoid crashes (mimic original intent but safer)
    if (o == -1) o = static_cast<int>(offers_.size()) - 1;
    if (b == -1) b = 0;

    double mid = (o + b) / 2.0;

    // bids from 0..floor(mid)
    int end_bids = static_cast<int>(std::floor(mid));
    for (int i = 0; i <= end_bids && i < static_cast<int>(bids_.size()); ++i) {
        ladder.emplace_back(static_cast<double>(i), bids_[i]);
    }
    // If mid has fractional, insert (mid, 0)
    if (std::fmod(mid, 1.0) != 0.0) {
        ladder.emplace_back(mid, 0.0);
    }
    // offers from ceil(mid)..end
    int start_offers = static_cast<int>(std::ceil(mid));
    for (int i = start_offers; i < static_cast<int>(offers_.size()); ++i) {
        ladder.emplace_back(static_cast<double>(i), offers_[i]);
    }

    return std::make_pair(ladder, mid);
}