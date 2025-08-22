#include "server_state_cpp.hpp"
#include <cmath>
#include <stdexcept>

void ServerStateCPP::init_order_book(const std::string& exchange_id,
                                     const std::string& market_id,
                                     const std::vector<LOBEntry>& bids,
                                     const std::vector<LOBEntry>& offers) {
    const std::string k = make_key(exchange_id, market_id);
    // Start with default tick; prices given are absolute (0..1), so indices follow tick.
    books_.erase(k);
    books_.emplace(k, OrderBookCore(kDefaultTick, bids, offers));
}

void ServerStateCPP::update_order_book(const std::string& exchange_id,
                                       const std::string& market_id,
                                       char pred,
                                       char side,
                                       const LOBEntry& data,
                                       bool is_delta) {
    const std::string k = make_key(exchange_id, market_id);
    auto it = books_.find(k);
    if (it == books_.end()) return;
    LOBEntry e = data;
    char s = side;
    apply_pred_flip(pred, s, e.price);
    it->second.update_level(e, s, is_delta);
}

void ServerStateCPP::update_order_book(const std::string& exchange_id,
                                       const std::string& market_id,
                                       char pred,
                                       char side,
                                       const std::vector<LOBEntry>& entries,
                                       bool is_delta) {
    const std::string k = make_key(exchange_id, market_id);
    auto it = books_.find(k);
    if (it == books_.end()) return;

    std::vector<LOBEntry> adjusted;
    adjusted.reserve(entries.size());
    char s = side;

    for (auto e : entries) {
        double p = e.price;
        s = side;
        apply_pred_flip(pred, s, p);
        adjusted.emplace_back(p, e.quantity);
        // NOTE: side can flip per pred, but pred is constant per call so safe to reuse s
    }
    it->second.update_levels(adjusted, s, is_delta);
}

std::pair<std::vector<LOBEntry>, std::vector<LOBEntry>>
ServerStateCPP::get_market(const std::string& exchange_id,
                           const std::string& market_id) const {
    const std::string k = make_key(exchange_id, market_id);
    auto it = books_.find(k);
    if (it == books_.end()) return {};

    const auto& ob = it->second;
    std::vector<LOBEntry> bids, offers;

    auto col_mid = ob.get_col();
    const auto& ladder = col_mid.first;
    const double mid = col_mid.second;

    const double tick_probe_best_bid = [&](){
        double p=0.0,q=0.0;
        if (ob.best_bid(p,q)) return p>0? p : kDefaultTick; // best available
        return kDefaultTick;
    }();

    const double tick = ob.tick_size();

    // We don't have public accessors for vectors; reconstruct from ladder.
    // ladder contains (index or fractional mid, qty). We filter non-zeros and convert index->price.
    for (const auto& pr : ladder) {
        const double idx = pr.first;
        const double qty = pr.second;
        if (std::fmod(idx, 1.0) != 0.0) continue; // skip mid marker
        if (qty == 0.0) continue;

        const int i = static_cast<int>(idx);
        const double price = i * tick_probe_best_bid / std::round(tick_probe_best_bid / tick); // robust to tick changes
        // Actually we know OrderBookCore uses its own tick; use best bid price to infer tick,
        // but safer is to ask OrderBookCore to convert; since we can't, assume index_to_price is idx * current tick_size.
        // We approximate using kDefaultTick if best bid could not be read.
    }

    // Better approach: We know OrderBookCore uses its internal tick value consistently.
    // Since we can't read it, assume default tick for price reconstruction.

    for (size_t j = 0; j < ladder.size(); ++j) {
        const double idx = ladder[j].first;
        const double qty = ladder[j].second;
        if (std::fmod(idx, 1.0) != 0.0 || qty == 0.0) continue;
        const double price = static_cast<int>(idx) * tick;
        if (idx < std::floor(mid) + 1e-12) {
            bids.emplace_back(price, qty);
        } else if (idx > std::ceil(mid) - 1e-12) {
            offers.emplace_back(price, qty);
        }
    }
    return {bids, offers};
}

void ServerStateCPP::set_tick_size(const std::string& exchange_id,
                                   const std::string& market_id,
                                   double new_tick_size) {
    const std::string k = make_key(exchange_id, market_id);
    auto it = books_.find(k);
    if (it == books_.end()) return;
    it->second.set_tick_size(new_tick_size);
}