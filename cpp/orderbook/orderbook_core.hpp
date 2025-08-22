#pragma once
#include <vector>
#include <cmath>
#include <algorithm>
#include <utility>

struct LOBEntry {
    double price;
    double quantity;
    LOBEntry() : price(0.0), quantity(0.0) {}
    LOBEntry(double p, double q) : price(p), quantity(q) {}
};

struct Trade {
    double price;
    double quantity;
    Trade() : price(0.0), quantity(0.0) {}
    Trade(double p, double q) : price(p), quantity(q) {}
};

class OrderBookCore {
public:
    OrderBookCore(double tick_size,
                  const std::vector<LOBEntry>& bids,
                  const std::vector<LOBEntry>& offers);

    void set_tick_size(double tick_size);

    // Returns true if present; outputs (price, qty)
    bool best_bid(double& price_out, double& qty_out) const;
    bool best_offer(double& price_out, double& qty_out) const;

    void update_level(const LOBEntry& entry, char side, bool is_delta);
    void update_levels(const std::vector<LOBEntry>& entries, char side, bool is_delta);

    std::vector<Trade> add_limit_order(const LOBEntry& entry, char side);
    
    double tick_size() const;

    // Ladder as (index, interest) and midpoint *index* (match original Python behavior)
    std::pair<std::vector<std::pair<double,double>>, double> get_col() const;
private:
    static inline int round_index(double x) {
        // Python round() differs on .5 ties; llround is OK for our price steps.
        return static_cast<int>(std::llround(x));
    }

    inline int price_to_index(double price) const {
        return round_index(price / tick_size_);
    }

    inline double index_to_price(int idx) const {
        return idx * tick_size_;
    }

    void rebuild_from_tick_change(double new_tick);

    double tick_size_;
    std::vector<double> bids_;
    std::vector<double> offers_;
};