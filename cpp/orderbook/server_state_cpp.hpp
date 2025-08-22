#pragma once
#include <unordered_map>
#include <string>
#include <vector>
#include <utility>
#include "orderbook_core.hpp"

class ServerStateCPP {
public:
    ServerStateCPP() = default;

    // Initialize or replace a book for (exchange, market)
    void init_order_book(const std::string& exchange_id,
                         const std::string& market_id,
                         const std::vector<LOBEntry>& bids,
                         const std::vector<LOBEntry>& offers);

    // Update book levels (handles pred 'y'/'n' semantics)
    void update_order_book(const std::string& exchange_id,
                           const std::string& market_id,
                           char pred,           // 'y' or 'n'
                           char side,           // 'b' or 'o'
                           const LOBEntry& data,
                           bool is_delta = false);

    void update_order_book(const std::string& exchange_id,
                           const std::string& market_id,
                           char pred,
                           char side,
                           const std::vector<LOBEntry>& entries,
                           bool is_delta = false);

    // Get nonzero bids/offers as price/qty pairs
    std::pair<std::vector<LOBEntry>, std::vector<LOBEntry>>
    get_market(const std::string& exchange_id,
               const std::string& market_id) const;

    // Change tick size of an existing book
    void set_tick_size(const std::string& exchange_id,
                       const std::string& market_id,
                       double new_tick_size);

private:
    static inline std::string make_key(const std::string& ex, const std::string& mar) {
        return ex + "|" + mar;
    }
    static inline void apply_pred_flip(char pred, char& side, double& price) {
        // Internally everything is from the "yes" perspective.
        if (pred == 'n') {
            price = 1.0 - price;
            if (side == 'b') side = 'o';
            else             side = 'b';
        }
    }

    // Defaults to 1 cent tick unless changed by a tick_size_change message
    static constexpr double kDefaultTick = 0.01;

    std::unordered_map<std::string, OrderBookCore> books_;
};