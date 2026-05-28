<template>
  <div class="task-module-main auction-shell card flex-grow-1 overflow-hidden d-flex flex-column">
    <div class="flex-grow-1 overflow-auto auction-shell__body">
      <div v-if="auctionsLoading" class="d-flex flex-wrap gap-3 p-2">
        <SkeletonLoader v-for="i in 6" :key="i" width="320px" height="200px" />
      </div>

      <div v-else-if="!auctions.length" class="d-flex flex-column align-center justify-center h-100 text-muted">
        <i class="fas fa-gavel fa-3x mb-3 text-light-gray"></i>
        <p>Нет активных аукционов</p>
      </div>

      <div v-else class="auction-grid">
        <div
          v-for="auction in auctions"
          :key="auction.id"
          class="auction-card"
          :class="['auction-' + auction.status, auction.is_block ? 'auction-card--block' : 'auction-card--single']"
        >
          <div class="auction-card-header">
            <div class="auction-card__header-main">
              <span class="auction-status-badge" :class="'status-' + auction.status">
                {{ getAuctionStatusText(auction.status) }}
              </span>
              <div class="auction-card__flags">
                <span v-if="auction.is_block" class="badge badge-outline-secondary badge-sm">Блок</span>
                <span v-if="auction.allow_custom_price" class="badge badge-outline-secondary badge-sm">Торг</span>
              </div>
            </div>
            <button
              v-if="canManageAuctions"
              class="btn btn-sm btn-icon text-danger auction-delete"
              title="Удалить"
              @click="deleteAuction(auction)"
            >
              <i class="fas fa-times"></i>
            </button>
          </div>
          <div class="auction-card__body">
            <h4 class="auction-title">{{ auction.title }}</h4>
            <p v-if="auction.description" class="auction-desc text-muted small">{{ auction.description }}</p>
            <div v-else class="auction-desc auction-desc--empty"></div>
            <div class="auction-meta">
              <div class="auction-budget">
                <span class="fw-600">{{ formatCurrency(auction.budget) }}</span>
              </div>
              <div class="auction-bids">
                <i class="fas fa-users"></i>
                <span>{{ auction.bids_count }} заявок</span>
              </div>
            </div>
            <div v-if="auction.is_block" class="auction-block">
              <button class="btn btn-sm btn-link auction-block-toggle" type="button" @click="toggleAuctionExpanded(auction.id)">
                <i class="fas" :class="isAuctionExpanded(auction.id) ? 'fa-chevron-up' : 'fa-chevron-down'"></i>
                Подзадачи ({{ auction.children?.length || 0 }})
              </button>
              <div v-if="isAuctionExpanded(auction.id)" class="auction-block-list">
                <div v-for="child in auction.children || []" :key="child.id" class="auction-subtask">
                  <button class="auction-subtask-toggle" type="button" @click="toggleSubtask(child.id)">
                    <div class="auction-subtask-main">
                      <div class="auction-subtask-title">{{ child.title }}</div>
                      <div class="auction-subtask-budget">{{ formatCurrency(child.budget) }}</div>
                    </div>
                    <div class="auction-subtask-tags">
                      <span v-if="child.allow_custom_price" class="badge badge-outline-secondary badge-sm">Торг</span>
                      <span class="badge badge-light badge-sm">{{ getAuctionStatusText(child.status) }}</span>
                      <span v-if="child.bids_count !== undefined" class="badge badge-light badge-sm">{{ child.bids_count }} заявок</span>
                    </div>
                  </button>
                  <div v-if="activeSubtaskId === child.id" class="auction-subtask-details">
                    <p v-if="child.description" class="text-muted small mb-2">{{ child.description }}</p>
                    <div class="auction-subtask-actions">
                      <button v-if="canManageAuctions" class="btn btn-sm btn-primary" @click.stop="viewAuctionBids(child)">
                        <i class="fas fa-eye mr-1"></i> Заявки
                      </button>
                      <button v-if="canBidAuctions && child.status === 'new'" class="btn btn-sm btn-success" @click.stop="submitBid(child)">
                        Взять
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="auction-block auction-block--spacer"></div>
          </div>
          <div class="auction-actions">
            <button v-if="canManageAuctions" class="btn btn-sm btn-primary flex-grow-1" @click="viewAuctionBids(auction)">
              <i class="fas fa-eye mr-1"></i> {{ auction.status === 'new' ? 'Заявки' : 'История' }}
            </button>
            <button v-if="canBidAuctions && auction.status === 'new'" class="btn btn-sm btn-success" @click="submitBid(auction)">
              {{ auction.allow_custom_price ? 'Предложить цену' : 'Взять' }}
            </button>
            <button v-if="canManageAuctions && auction.status === 'new'" class="btn btn-sm btn-icon text-danger" @click="cancelAuction(auction)" title="Отменить">
              <i class="fas fa-times"></i>
            </button>
            <div v-else-if="canManageAuctions" class="auction-actions__placeholder"></div>
            <div v-else-if="canBidAuctions" class="auction-actions__placeholder"></div>
            <div v-else class="auction-actions__placeholder"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import SkeletonLoader from '../../../components/ui/SkeletonLoader.vue'

export default {
  name: 'TaskAuctions',
  components: { SkeletonLoader },
  props: { state: { type: Object, required: true } },
  setup(props) {
    return { ...props.state }
  }
}
</script>
